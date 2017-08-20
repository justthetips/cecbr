import base64
import os
import uuid

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from cecbr.core.models import TimeStampedModel


def training_directory_path(instance, filename):
    return 'person_{0}/{1}'.format(instance.person.name, filename)


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
        salt = self._cecbr_salt
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(u_password))
        f = Fernet(key)
        return f.decrypt(self.cecbr_password)

    def save(self, *args, **kwargs):
        if not self._cecbr_pwd_set:
            self.handle_pwd(self.cecbr_password)
        super(CECBRProfile, self).save(*args, **kwargs)

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

    album_count = property(_get_album_count)

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

    def __str__(self):
        return self.album_name

    def album_url(self, base_url: str) -> str:
        season_param = '='.join(['seasonID', self.season.season_name])
        album_param = '='.join(['albumID', str(self.id)])
        full_url = '?'.join([base_url, '&'.join([season_param, album_param])])
        return full_url

    class Meta:
        verbose_name = 'Album'
        verbose_name_plural = 'Albums'
        ordering = ['season', '-album_date']


class Photo(TimeStampedModel):
    album = models.ForeignKey(Album)
    photo_id = models.CharField(max_length=32, primary_key=True)
    small_url = models.URLField(blank=False)
    large_url = models.URLField(blank=False)
    face_json = JSONField(blank=True)
    people_json = JSONField(blank=True)
    analyzed = models.BooleanField(default=False)
    analyzed_date = models.DateTimeField(blank=True, null=True)
    identified = models.BooleanField(default=False)
    identified_date = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return "Photo {} from Album {}".format(self.id, self.album.album_name)

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
    face_json = JSONField(blank=False)
