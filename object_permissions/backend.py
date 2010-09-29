from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from object_permissions.models import ObjectPermission, ObjectPermissionType


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
        p = ObjectPermission.objects.filter(permission__content_type=ct,
                                            object_id=obj.id,
                                            user=user_obj)
        return p.filter(permission__name=perm).exists()