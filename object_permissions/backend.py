from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from object_permissions.models import ObjectPermission, ObjectPermissionType, \
    GroupObjectPermission


class ObjectPermBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def authenticate(self, username, password):
        """ Empty method, this backend does not authenticate users """
        return None

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_authenticated():
            user_obj = User.objects.get(pk=settings.ANONYMOUS_USER_ID)
        
        if obj is None:
            return False
        
        ct = ContentType.objects.get_for_model(obj)        
        user_perm = ObjectPermission.objects.filter(permission__content_type=ct,
                                            object_id=obj.id,
                                            user=user_obj)
        if user_perm.filter(permission__name=perm).exists():
            return True
        
        group_perm = GroupObjectPermission.objects \
                        .filter(permission__content_type=ct, object_id=obj.id, \
                                group__users__id=user_obj.id)
        return group_perm.filter(permission__name=perm).exists()