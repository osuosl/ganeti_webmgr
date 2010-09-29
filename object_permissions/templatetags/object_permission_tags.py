from django.template import Library

from object_permissions.registration import get_user_perms

register = Library()

@register.filter
def permissions(user, object):
    """
    Returns the list of permissions a user has on an object
    """
    return get_user_perms(user, object)