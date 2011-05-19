from django.template import Library

from object_permissions.registration import get_users_all

register = Library()


@register.simple_tag
def number_group_admins(group):
    "Return number of users with admin perms for specified group"
    return get_users_all(group, ["admin",], False).count()