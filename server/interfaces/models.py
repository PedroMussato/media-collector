from django.db import models
from django.contrib.auth.models import User
import uuid

class Band(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default='')
    uuid = models.UUIDField(default = uuid.uuid4)

class Album(models.Model):
    band = models.ForeignKey(Band, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default='')
    uuid = models.UUIDField(default = uuid.uuid4)
    cover = models.ImageField(upload_to="covers/", default=None, null=True)

class Music(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default='')
    track = models.IntegerField(null=True)
    yt_url = models.URLField(blank=True)
    uuid = models.UUIDField(default = uuid.uuid4)
