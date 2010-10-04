from django.conf.urls.defaults import *

urlpatterns = patterns('ganeti_webmgr.object_permissions.views.user_groups',
    # UserGroups
    url(r'^user_group/(?P<id>\d+)/?$',
        'detail', name="user_group-detail"),
    url(r'^user_group/(?P<id>\d+)/user/add/?$',
        'add_user', name="user_group-add-user"),
    url(r'^user_group/(?P<id>\d+)/user/remove/?$',
        'remove_user', name="user_group-remove-user"),
    url(r'^user_group/(?P<id>\d+)/user/$',
        'user_permissions', name="user_group-user-permissions"),
)