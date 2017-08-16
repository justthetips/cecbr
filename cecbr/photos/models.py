from django.conf import settings
from django.db import models

from cecbr.core.models import TimeStampedModel

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CECBRProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    _cecbr_pwd_set = models.BooleanField(default=False)
    cecbr_uname = models.CharField(max_length=128, blank=True)
    cecbr_password = models.CharField(max_length=256, blank=True)
    last_album_view = models.DateTimeField(blank=True, null=True)
    _cecbr_salt = models.BinaryField(blank=True)

    def handle_pwd(self, raw_password):
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

    def get_pwd(self):
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

