import uuid

from django.db import models

from cecbr.core.models import TimeStampedModel
from cecbr.photos.models import CECBRProfile, Photo


def photo_directory_path_s(instance, filename):
    return 'user_{0}/season_{1}/album_{2}/small/{3}'.format(instance.user.id, instance.photo.album.season,
                                                            instance.photo.album.id, filename)


def photo_directory_path_l(instance, filename):
    return 'user_{0}/season_{1}/album_{2}/full/{3}'.format(instance.user.id, instance.photo.album.season,
                                                           instance.photo.album.id, filename)


class VaultedPhoto(TimeStampedModel):
    user = models.ForeignKey(CECBRProfile)
    photo = models.ForeignKey(Photo)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    small_photo = models.ImageField(upload_to='photo_directory_path_s', null=True, blank=True,
                                    verbose_name=u'Small Image')
    large_photo = models.ImageField(upload_to='photo_directory_path_l', null=True, blank=True,
                                    verbose_name=u'large Image')

    def __str__(self):
        return 'Vault-{}'.format(self.photo.__str__())
