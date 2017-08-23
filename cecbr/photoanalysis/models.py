from django.db import models
from django.conf import settings

from cecbr.core.models import TimeStampedModel
from cecbr.photos.models import Group

class AnalysisGroup(TimeStampedModel):

    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    trainer = models.FileField(blank=True)
    trained = models.BooleanField(default=False)
    trained_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Analysis Group for {}".format(self.group.group_name)

class AnalysisPhoto(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    group = models.ManyToManyField(AnalysisGroup)
    label = models.CharField(max_length=128, blank=False, null=False)
    raw_photo = models.ImageField(blank=False, null=False)
    detected_photo = models.ImageField(blank=True, null=True)
    face_photo = models.ImageField(blank=True, null=True)
    detected = models.BooleanField(default=False)
    detected_date = models.DateTimeField(blank=True, null=True)
    faced = models.BooleanField(default=False)
    faced_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Photo for {}".format(self.label)






