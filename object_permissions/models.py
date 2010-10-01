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


class UserGroup(models.Model):
    """
    A UserGroup is used to group people together, and then give them common
    permissions on an object.  This is useful when an organization has many
    users and you want to control access via membership in the organization.
    """
    name = models.CharField(max_length=64, unique=True)
    users = models.ManyToManyField(User, related_name="user_groups",
                                   null=True, blank=True)


class GroupObjectPermission(models.Model):
    group = models.ForeignKey(UserGroup, related_name='user_groups')
    permission = models.ForeignKey(ObjectPermissionType)
    object_id = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ("group", "permission", "object_id")


class PermissionTypeGroup(models.Model):
    """
    A PermissionGroup is a group of permisssions types that can be granted
    granted to a User/Object.
    
    XXX this object has not been defined yet, but exists to illustrate the
    difference between PermissionGroup and UserGroup
    """
    pass