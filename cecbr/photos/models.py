import base64
import json
import logging
import os
import uuid

import django.utils.timezone
import requests

from urllib.parse import urlparse
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.query import QuerySet

from cecbr.core.models import TimeStampedModel
from cecbr.photoanalysis.util import find_face, face_encodings
from cecbr.photos.utils import parsers, cecbrsite
from cecbr.photos.utils.cecbrsite import Page

logger = logging.getLogger(__name__)


def training_directory_path(instance, filename):
    return 'person_{0}/{1}'.format(instance.person.name, filename)

def photo_directory_path_s(instance, filename):
    return 'user_{0}/season_{1}/album_{2}/small/{3}'.format(instance.user.id, instance.photo.album.season.season_name,
                                                            instance.photo.album.album_id, filename)


def photo_directory_path_l(instance, filename):
    return 'user_{0}/season_{1}/album_{2}/full/{3}'.format(instance.user.id, instance.photo.album.season.season_name,
                                                           instance.photo.album.album_id, filename)


class CECBRProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    _cecbr_pwd_set = models.BooleanField(default=False)
    cecbr_uname = models.CharField(max_length=128, blank=True)
    cecbr_password = models.CharField(max_length=256, blank=True)
    last_album_view = models.DateTimeField(blank=True, null=True)
    _cecbr_salt = models.BinaryField(blank=True)

    def handle_pwd(self, raw_password: str) -> None:
        b_password = str.encode(raw_password)
        u_password = str.encode(settings.SECRET_KEY)
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(u_password))
        f = Fernet(key)
        c_pwd = f.encrypt(b_password)
        self.cecbr_password = c_pwd
        self._cecbr_salt = salt
        self._cecbr_pwd_set = True

    def get_pwd(self) -> str:
        u_password = str.encode(settings.SECRET_KEY)
        salt = bytes(self._cecbr_salt)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(u_password))
        f = Fernet(key)
        plain_pwd = f.decrypt(str.encode(self.cecbr_password))
        return plain_pwd.decode("utf-8")

    def save(self, *args, **kwargs):
        if not self._cecbr_pwd_set:
            self.handle_pwd(self.cecbr_password)
        super(CECBRProfile, self).save(*args, **kwargs)

    def get_favorites(self, season):
        logger.info("Loading favorites for {} in season {}".format(self.user.name, season))
        logon_page = parsers.get_logged_on_page(self.cecbr_uname, self.get_pwd())
        favorite_photos = parsers.get_favorites(logon_page, season)
        for favorite_photo in favorite_photos:
            photo = Photo.objects.get(photo_id=favorite_photo.id)
            photo.favorite_photo(self)


    def __str__(self):
        return self.user.name

    class Meta:
        verbose_name = 'CECBR Profile'
        verbose_name_plural = 'CECBR Profiles'


class Season(TimeStampedModel):
    season_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    season_name = models.CharField(max_length=32, blank=False, null=False)

    def __str__(self):
        return self.season_name

    def _get_album_count(self) -> int:
        return Album.objects.filter(season=self).count()

    def _get_photo_count(self) -> int:
        photo_count = 0
        albums = Album.objects.filter(season=self)
        for album in albums:
            photo_count += album.count
        return photo_count

    album_count = property(_get_album_count)
    photo_count = property(_get_photo_count)

    def season_url(self, base_url: str) -> str:
        season_param = '='.join(['seasonID', self.season_name])
        full_url = '?'.join([base_url, season_param])
        return full_url

    def process_season(self, profile: CECBRProfile) -> None:
        logger.info("Processing Season {}".format(self.season_name))
        logon_page = parsers.get_logged_on_page(profile.cecbr_uname, profile.get_pwd())
        albums = parsers.get_season_index(logon_page, self.season_url(cecbrsite.SEASON_URL))
        for album in albums:
            if Album.objects.filter(album_id=album.id).exists():
                logger.debug("Album {} exists, checking to see if photo count changed".format(album.name))
                old_album = Album.objects.get(album_id=album.id)
                if old_album.count != album.count:
                    logger.info(
                        "Album {}'s photo count changed, it went from {} to {}".format(album.name, old_album.count,
                                                                                       album.count))
                    old_album.count = album.count
                    old_album.processed = False
                    old_album.analyzed = False
                    old_album.processed_date = None
                    old_album.analyzed_date = None
                    old_album.save()
            else:
                logger.info("Adding new album {}".format(album.name))
                new_album = Album(season=self, album_id=album.id, album_name=album.name, cover_url=album.cover_url,
                                  count=album.count,
                                  album_date=album.al_date)
                new_album.save()

    class Meta:
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'
        ordering = ['-season_name']


class Album(TimeStampedModel):
    season = models.ForeignKey(Season)
    album_id = models.CharField(max_length=32, primary_key=True, blank=False, null=False)
    album_name = models.CharField(max_length=128, blank=False, null=False)
    album_date = models.DateField(blank=False, null=False)
    count = models.IntegerField(blank=False, null=False)
    processed = models.BooleanField(default=False)
    processed_date = models.DateTimeField(blank=True, null=True)
    analyzed = models.BooleanField(default=False)
    analyzed_date = models.DateTimeField(blank=True, null=True)
    cover_url = models.URLField(blank=False, null=False)

    def __str__(self):
        return self.album_name

    def album_url(self, base_url: str) -> str:
        season_param = '='.join(['seasonID', self.season.season_name])
        album_param = '='.join(['albumID', str(self.album_id)])
        full_url = '?'.join([base_url, '&'.join([season_param, album_param])])
        return full_url

    def process_album(self, profile: CECBRProfile, logon_page: Page = None) -> None:
        logger.info("Processing Album {} it has {} photos".format(self.album_name, self.count))
        if logon_page is None:
            logon_page = parsers.get_logged_on_page(profile.cecbr_uname, profile.get_pwd())
        photos = parsers.get_album(logon_page, self.album_url(cecbrsite.ALBUM_URL))
        for photo in photos:
            if not Photo.objects.filter(photo_id=photo.id).exists():
                logger.debug('Photo {} is new, adding it'.format(photo.id))
                photo = Photo(album=self, photo_id=photo.id, small_url=photo.small_url, large_url=photo.large_url)
                photo.save()
        self.processed = True
        self.processed_date = django.utils.timezone.now()
        self.save()

    @staticmethod
    def process_albums(self, profile: CECBRProfile, albums: QuerySet) -> None:
        logger.info("Processing {} albums".format(albums.count()))

        logon_page = parsers.get_logged_on_page(profile.cecbr_uname, profile.get_pwd())
        for album in albums:
            album.process_album(profile, logon_page)

    class Meta:
        verbose_name = 'Album'
        verbose_name_plural = 'Albums'
        ordering = ['season', '-album_date']


class Photo(TimeStampedModel):
    album = models.ForeignKey(Album)
    photo_id = models.CharField(max_length=32, primary_key=True)
    small_url = models.URLField(blank=False)
    large_url = models.URLField(blank=False)
    face_json = JSONField(blank=True, null=True)
    people_json = JSONField(blank=True, null=True)
    analyzed = models.BooleanField(default=False)
    analyzed_date = models.DateTimeField(blank=True, null=True)
    identified = models.BooleanField(default=False)
    identified_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return "Photo {} from Album {}".format(self.photo_id, self.album.album_name)

    def analyze_photo(self):
        locations = json.loads(find_face(self.large_url))
        encodings = json.loads(face_encodings(self.large_url))
        d = {'locations': locations, 'encodings': encodings}
        self.face_json = json.dumps(d)
        self.analyzed = True
        self.analyzed_date = django.utils.timezone.now()
        self.save()

    def vault_photo(self,user: CECBRProfile):
        vp = VaultedPhoto(user=user, photo=self)
        small_name = urlparse(self.small_url).path.split('/')[-1]
        large_name = urlparse(self.large_url).path.split('/')[-1]
        small_response = requests.get(self.small_url)
        large_response = requests.get(self.large_url)
        vp.small_photo.save(name=small_name,content=ContentFile(small_response.content), save=True)
        vp.large_photo.save(name=large_name, content=ContentFile(large_response.content), save=True)
        vp.save()
        return vp

    def favorite_photo(self,user: CECBRProfile):
        vp = self.vault_photo(user)
        vp.is_favorite = True
        vp.save()
        return vp

    class Meta:
        ordering = ['album', 'photo_id']
        verbose_name = 'Photo'
        verbose_name_plural = 'Photos'


class Group(TimeStampedModel):
    user = models.ForeignKey(CECBRProfile)
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_name = models.CharField(max_length=128, blank=False, null=False)
    trained = models.BooleanField(default=False)
    trained_date = models.DateTimeField(blank=True, null=True)
    analyzed_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.group_name


class Person(TimeStampedModel):
    groups = models.ManyToManyField(Group)
    person_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person_name = models.CharField(max_length=128, blank=False, null=False)
    photos = models.ManyToManyField(Photo)

    def __str__(self) -> str:
        return self.person_name


class TrainingPhoto(TimeStampedModel):
    person = models.ForeignKey(Person)
    photo = models.ImageField(upload_to=training_directory_path, null=False, blank=False)
    face_json = JSONField(blank=False, null=True)

class VaultedPhoto(TimeStampedModel):
    user = models.ForeignKey(CECBRProfile)
    photo = models.ForeignKey(Photo)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    small_photo = models.ImageField(upload_to=photo_directory_path_s, null=True, blank=True,
                                    verbose_name=u'Small Image')
    large_photo = models.ImageField(upload_to=photo_directory_path_l, null=True, blank=True,
                                    verbose_name=u'large Image')
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return 'Vault-{}'.format(self.photo.__str__())

