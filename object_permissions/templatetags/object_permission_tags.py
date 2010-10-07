from django.template import Library

from object_permissions.registration import get_user_perms

register = Library()

@register.filter
def permissions(user, object):
    """
    Returns the list of permissions a user has on an object
    """
    if user:
        return user.get_perms(object)
    return []