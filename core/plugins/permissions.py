from django.contrib.auth.models import User

from core.models import Permission, PermissionGroup, Permissable, Group, \
                    UserProfile
from core.plugins.plugin import Plugin
from core.plugins.model_support import ModelView, ModelListView


class PermissionsPlugin(Plugin):
    """
    Plugin that registers Permissions objects for viewing and editing
    """
    objects = (
        # Register Objects
        
        PermissionGroup,
        Permissable,
        Group,
        User,
        UserProfile,
        Permission,
        
        # Register Views
        ModelView(Permission),
        ModelView(UserProfile),
        ModelView(Group),
        ModelListView(UserProfile),
        ModelListView(Group)
    )

