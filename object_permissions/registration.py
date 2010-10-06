from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django import db
from django.db import models

from models import ObjectPermission, ObjectPermissionType, UserGroup, \
    GroupObjectPermission
import object_permissions


_DELAYED = []

def register(perm, model):
    """
    Register a permission for a Model.  This will insert a row into the
    permission table if one does not already exist.
    """
    try:
        _register(perm, model)
    except db.utils.DatabaseError:
        # there was an error, likely due to a missing table.  Delay this
        # registration.
        _DELAYED.append((perm, model))


def _register(perm, model):
    """
    Real method for registering permissions.  This inner function is used
    because it must also be called back from _register_delayed
    """
    ct = ContentType.objects.get_for_model(model)
    obj, new = ObjectPermissionType.objects \
               .get_or_create(name=perm, content_type=ct)
    if new:
        obj.save()


def _register_delayed(**kwargs):
    """
    Register all permissions that were delayed waiting for database tables
    to be created
    """
    try:
        for args in _DELAYED:
            _register(*args)
        models.signals.post_syncdb.disconnect(_register_delayed)
    except db.utils.DatabaseError:
        # still waiting for models in other apps to be created
        pass

models.signals.post_syncdb.connect(_register_delayed)

def grant(user, perm, object):
    """
    Grants a permission to a User
    """
    ct = ContentType.objects.get_for_model(object)
    pt = ObjectPermissionType.objects.get(name=perm, content_type=ct)
    properties = dict(user=user, permission=pt, object_id=object.id)
    if not ObjectPermission.objects.filter(**properties).exists():
        ObjectPermission(**properties).save()


def grant_group(group, perm, object):
    """
    Grants a permission to a UserGroup
    """
    ct = ContentType.objects.get_for_model(object)
    pt = ObjectPermissionType.objects.get(name=perm, content_type=ct)
    properties = dict(group=group, permission=pt, object_id=object.id)
    if not GroupObjectPermission.objects.filter(**properties).exists():
        GroupObjectPermission(**properties).save()


def revoke(user, perm, object):
    """
    Revokes a permission from a User
    """
    ct = ContentType.objects.get_for_model(object)
    ObjectPermission.objects \
        .filter(user=user, object_id=object.id,  \
                permission__content_type=ct, permission__name=perm) \
        .delete()


def revoke_all(user, object):
    """
    Revokes all permissions from a User
    """
    ct = ContentType.objects.get_for_model(object)
    ObjectPermission.objects \
        .filter(user=user, object_id=object.id, permission__content_type=ct) \
        .delete()


def revoke_group(group, perm, object):
    """
    Revokes a permission from a UserGroup
    """
    ct = ContentType.objects.get_for_model(object)
    GroupObjectPermission.objects \
        .filter(group=group, object_id=object.id,  \
                permission__content_type=ct, permission__name=perm) \
        .delete()


def get_user_perms(user, object):
    """
    Return a list of perms that a User has.
    """
    ct = ContentType.objects.get_for_model(object)
    query = ObjectPermission.objects \
        .filter(user=user, object_id=object.id, permission__content_type=ct) \
        .values_list('permission__name', flat=True)
    return list(query)


def get_group_perms(group, object):
    """
    Return a list of perms that a UserGroup has.
    """
    ct = ContentType.objects.get_for_model(object)
    query = GroupObjectPermission.objects \
        .filter(group=group, object_id=object.id, permission__content_type=ct) \
        .values_list('permission__name', flat=True)
    return list(query)


def get_model_perms(model):
    """
    Return a list of perms that a model has registered
    """
    ct = ContentType.objects.get_for_model(model)
    query = ObjectPermissionType.objects.filter(content_type=ct) \
            .values_list('name', flat=True)
    return list(query)


def get_users(object):
    """
    Return a list of users with permissions on a given object
    """
    ct = ContentType.objects.get_for_model(object)
    return User.objects.filter(
            object_permissions__permission__content_type=ct, \
            object_permissions__object_id=object.id).distinct()


# register internal perms
register('admin', UserGroup)


# make some methods available as bound methods
setattr(User, 'grant', grant)
setattr(User, 'revoke', revoke)
setattr(User, 'revoke_all', revoke_all)
setattr(User, 'get_perms', get_user_perms)

setattr(UserGroup, 'grant', grant_group)
setattr(UserGroup, 'revoke', revoke_group)
setattr(UserGroup, 'get_perms', get_group_perms)