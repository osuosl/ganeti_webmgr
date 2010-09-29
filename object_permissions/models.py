from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType


class ObjectPermissionType(models.Model):
    name = models.CharField(max_length=64)
    content_type = models.ForeignKey(ContentType)
    
    class Meta:
        unique_together = ("name", "content_type")


class ObjectPermission(models.Model):
    user = models.ForeignKey(User)
    permission = models.ForeignKey(ObjectPermissionType)
    object_id = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ("user", "permission", "object_id")