from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from models import ObjectPermission, ObjectPermissionType, UserGroup, \
    GroupObjectPermission



def register(perm, model):
    """
    Register a permission for a Model.  This will insert a row into the
    permission table if one does not already exist.
    """
    ct = ContentType.objects.get_for_model(model)
    obj, new = ObjectPermissionType.objects \
               .get_or_create(name=perm, content_type=ct)
    if new:
        obj.save()


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
    
    
# make some methods available as bound methods
setattr(User, 'grant', grant)
setattr(User, 'revoke', revoke)
setattr(User, 'get_perms', get_user_perms)

setattr(UserGroup, 'grant', grant_group)
setattr(UserGroup, 'revoke', revoke_group)
setattr(UserGroup, 'get_perms', get_group_perms)