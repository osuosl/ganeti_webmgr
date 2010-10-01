from django.conf import settings
from django.conf.urls.defaults import *

cluster = 'cluster/(?P<cluster_slug>\w+)'
instance = '/(?P<instance>[^/]+)'

urlpatterns = patterns('ganeti_webmgr.ganeti.views.general',
    # Example:
    # (r'^ganeti_webmgr/', include('ganeti_webmgr.foo.urls')),
    url(r'^$', 'index', name="cluster-overview"),
    #   Orphans
    url(r'^orphans/','orphans', name='instance-orphans'),
    # Authentication
    url(r'^accounts/login/?', 'login_view', name="login"),
    url(r'^accounts/logout/?', 'logout_view', name="logout"),
)

# Clusters
urlpatterns += patterns('ganeti_webmgr.ganeti.views.cluster',
    #   List
    url(r'^clusters/', 'list', name="cluster-list"),
    #   Detail
    url(r'^' + cluster + '$', 'detail', name="cluster-detail"),
)

# Instances
urlpatterns += patterns('ganeti_webmgr.ganeti.views.instances',
    #  List
    #  Detail
    url(r'^' + cluster + instance, 'detail', name="instance-detail"),
    #  Create
    url(r'^' + cluster + '/create/?$',
        'create', name="instance-create"),
    #  Start, Stop, Reboot
    url(r'^' + cluster + instance + '/vnc/?$',
        'vnc', name="instance-vnc"),
    url(r'^' + cluster + instance + '/shutdown/?$',
        'shutdown', name="instance-shutdown"),
    url(r'^' + cluster + instance + '/startup/?$',
        'startup', name="instance-startup"),
    url(r'^' + cluster + instance + '/reboot/?$',
        'reboot', name="instance-reboot"),
)

urlpatterns += patterns('ganeti_webmgr.ganeti.organizations',
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