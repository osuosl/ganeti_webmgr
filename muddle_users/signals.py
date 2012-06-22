from django.conf import settings
from django.dispatch import Signal

# XXX use signals from object permissions if it's available.  It should be, but
# we might not use it for all apps.
if 'object_permissions' in settings.INSTALLED_APPS:
    from object_permissions.signals import view_add_user, view_edit_user, \
        view_remove_user
else:
    # sent when a user has been added to a group
    view_add_user = Signal(providing_args=["editor", "user", "obj"])

    # sent when a user has been remove from a group
    view_remove_user = Signal(providing_args=["editor", "user", "obj"])

    # send when a user's permissions have been edited
    view_edit_user = Signal(providing_args=["editor", "user", "obj"])


#
# Signals issued when a group is edited
#
view_group_created = Signal(providing_args=["editor"])

view_group_edited = Signal(providing_args=["editor"])

view_group_deleted = Signal(providing_args=["editor"])