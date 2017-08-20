import logging
import os
import time
from abc import ABCMeta, abstractmethod
from typing import Tuple, Dict

import attr
from bs4 import BeautifulSoup
from django.conf import settings
from selenium import webdriver

# CAMP BASE URLS
LOGON_URL = "https://blueridge.campintouch.com/v2/login/login.aspx"
SEASON_URL = "https://blueridge.campintouch.com/ui/photo/Albums"
ALBUM_URL = "https://blueridge.campintouch.com/ui/photo/Thumbnails"

# Get an instance of a logger
logger = logging.getLogger(__name__)


@attr.s
class Page(object):
    logon_page = attr.ib(default=LOGON_URL, validator=attr.validators.instance_of(str))
    initialized = False
    logged_in = False
    driver_path = attr.ib(default=settings.PHANTOM_PATH, validator=attr.validators.instance_of(str))

    def __init__(self, user_name: str, password: str):
        self._user_name = user_name
        self._password = password
        self._driver = None

    def driver(self, check_initialized: bool = True) -> webdriver:
        if check_initialized:
            if not self.initialized:
                self.initialize()
            if not self.logged_in:
                self.logon()

        return self._driver

    def initialize(self):
        self._driver = webdriver.PhantomJS(executable_path=self.driver_path, service_log_path=os.path.devnull)
        self.initialized = True

    def logon(self):
        if not self.initialized:
            self.initialize()

        logger.info("Attempting to log in to {}".format(self.logon_page))
        self._driver.get(self.logon_page)

        # now handle the form
        user_tb = self._driver.find_element_by_name('txtEmail')
        user_tb.clear()
        user_tb.send_keys(self._user_name)
        pw_tb = self._driver.find_element_by_name('txtPassword')
        pw_tb.clear()
        pw_tb.send_keys(self._password)
        # submit
        submit_bttn = self._driver.find_element_by_id('btnLogin')
        submit_bttn.click()
        time.sleep(7)
        self.logged_in = True

    def close(self):
        if self._driver is not None:
            self._driver.close()
        self.initialized = False
        self.logged_in = False

    def retrieve_page(self, url: str) -> webdriver:
        if not self.logged_in:
            self.logon()
        self._driver.get(url)
        return self._driver

    def retrieve_html(self, url: str) -> str:
        return self.retrieve_page(url).page_source


class CampMinderPhotoFinder(metaclass=ABCMeta):
    array_search_string = attr.ib(default='AlbumArray', validator=attr.validators.instance_of(str))
    front_clean_chars = attr.ib(default=1, validator=attr.validators.instance_of(int))
    main_dict_key = attr.ib(default='AlbumID', validator=attr.validators.instance_of(str))

    def __init__(self, logon_page: Page, url: str, *args: str, **kwargs: str) -> None:
        self._logon_page = logon_page
        self._url = url

    @abstractmethod
    def prettify(self, string: str) -> str:
        pass

    def parse(self) -> Dict[str, dict]:

        if not self._logon_page.logged_in:
            self._logon_page.logon()

        dicts = {}
        page_html = self._logon_page.retrieve_html(self._url)

        # use beautiful soup for parsing
        soup = BeautifulSoup(page_html, 'html.parser')
        scripts = soup.find_all(script_with_no_src)
        for script in scripts:
            if self.array_search_string in script.text:
                dicts = self.read_pretified_to_dict(self.build_album_array_string(script.text))

        return dicts

    @staticmethod
    def split_token(token: str) -> Tuple[str, str]:
        split_pos = token.find(":")
        if split_pos == -1:
            raise ValueError("%s is not a valid key.value token" % token)
        key = token[0:split_pos].replace('{', '').replace('"', '')
        value = token[split_pos + 1:].replace('\\', '')
        return key, value

    def read_pretified_to_dict(self, pretty_string: str) -> Dict[str, dict]:
        dicts = {}
        for row in pretty_string.split('\n'):
            if len(row) != 1:
                local_dict = {}
                decoded = row.replace('\\', '')
                cleaned = decoded[self.front_clean_chars:(len(decoded) - 1)]
                tokens = cleaned.split(',')
                for token in tokens:
                    try:
                        (key, value) = self.split_token(token)
                        local_dict[key] = value
                    except ValueError:
                        logger.debug("token %s does not parse correctly" % token)
                dicts[local_dict[self.main_dict_key]] = local_dict
        return dicts

    def build_album_array_string(self, string: str) -> str:
        logger.info("Attepmting to extract javascript album")
        start_album_array = string.find(self.array_search_string)
        if start_album_array == -1:
            raise ValueError("String does not contain {}".format(self.array_search_string))
        start_album_array += len(self.array_search_string)
        # find the opening '['
        pos = string.find('[', start_album_array)
        if pos == -1:
            raise ValueError("Not a valid camp minder album string")
        bracket_count = 1
        char_list = ['[']
        pos += 1
        while bracket_count != 0 or pos == len(string):
            c = string[pos]
            if c == '[':
                bracket_count += 1
            elif c == ']':
                bracket_count -= 1
            char_list.append(c)
            pos += 1
        return self.prettify(''.join(char_list))


class IndexAlbumParser(CampMinderPhotoFinder):
    def __init__(self, logon_page: Page, url: str, *args: str, **kwargs: str) -> None:
        super().__init__(logon_page, url, *args, **kwargs)

    def prettify(self, string):
        pos = 0
        pretty_array = []
        while pos < len(string):
            c = string[pos]
            pretty_array.append(c)
            if c == '}':
                pretty_array.append('\n')
            pos += 1
            if pos == 1:
                pretty_array.append('\n,')
        return ''.join(pretty_array)


class FavoriteAlbumParser(CampMinderPhotoFinder):
    def __init__(self, logon_page: Page, url: str, *args: str, **kwargs: str) -> None:
        super().__init__(logon_page, url, *args, **kwargs)
        self.array_search_string = kwargs.get('array_search_string', 'CurrentAlbum')
        self.front_clean_chars = kwargs.get('front_clean_chars', 2)
        self.main_dict_key = kwargs.get('main_dict_key', 'PhotoID')

    def prettify(self, string):
        pos = 0
        pretty_array = []
        brck_count = 0
        while pos < len(string):
            c = string[pos]
            pretty_array.append(c)
            if c == '{':
                brck_count += 1
            if c == '}':
                brck_count -= 1
                if brck_count == 0:
                    pretty_array.append('\n')
            pos += 1
            if pos == 1:
                pretty_array.append('\n,')
        return ''.join(pretty_array)


def script_with_no_src(tag):
    return tag.name == 'script' and not tag.has_attr('src')


def unquote(string: str) -> str:
    if string.startswith('"') and string.endswith('"'):
        string = string[1:-1]
    return string
