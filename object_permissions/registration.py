from models import ObjectPermission, ObjectPermissionType 
from django.contrib.contenttypes.models import ContentType


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
    Grants a permission to a user
    """
    ct = ContentType.objects.get_for_model(object)
    pt = ObjectPermissionType.objects.get(name=perm, content_type=ct)
    properties = dict(user=user, permission=pt, object_id=object.id)
    if not ObjectPermission.objects.filter(**properties).exists():
        ObjectPermission(**properties).save()


def revoke(user, perm, object):
    """
    Revokes a permission from a user
    """
    ct = ContentType.objects.get_for_model(model)
    ObjectPermission.objects \
        .filter(user=user, permission__content_type=ct, name=perm).delete()


def get_user_perms(user, object):
    """
    Return a list of perms that a user has.
    """
    ct = ContentType.objects.get_for_model(object)
    query = ObjectPermission.objects \
        .filter(user=user, object_id=object.id, permission__content_type=ct) \
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