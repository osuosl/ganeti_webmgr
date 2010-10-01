from django.conf.urls.defaults import *

urlpatterns = patterns('ganeti_webmgr.object_permissions.organizations',
    # Organizations
    url(r'^organization/(?P<id>\d+)/?$',
        'detail', name="organization-detail"),
    url(r'^organization/(?P<id>\d+)/user/add/?$',
        'add_user', name="organization-add-user"),
    url(r'^organization/(?P<id>\d+)/user/remove/?$',
        'remove_user', name="organization-remove-user"),
    url(r'^organization/(?P<id>\d+)/user/(?P<user_id>\d+)/?$',
        'user_permissions', name="organization-user-permissions"),
)