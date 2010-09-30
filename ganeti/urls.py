from django.conf import settings
from django.conf.urls.defaults import *

cluster = 'cluster/(?P<cluster_slug>\w+)'
instance = '/(?P<instance>[^/]+)'

urlpatterns = patterns('ganeti_webmgr.ganeti.views',
    # Example:
    # (r'^ganeti_webmgr/', include('ganeti_webmgr.foo.urls')),
    url(r'^/?$',
        'general.index', name="cluster-overview"),
        
    # Cluster
    #   List
    url(r'^clusters/',
        'cluster.list', name="cluster-list"),
    #   Detail
    url(r'^' + cluster + '$',
        'cluster.detail', name="cluster-detail"),
    # Instance
    #  List
    #  Detail
    url(r'^' + cluster + instance,
        'instances.detail', name="instance-detail"),
    #  Create
    url(r'^' + cluster + '/create/?$',
        'instances.create', name="instance-create"),
    #  Start, Stop, Reboot
    url(r'^' + cluster + instance + '/vnc/?$',
        'instances.vnc', name="instance-vnc"),
    url(r'^' + cluster + instance + '/shutdown/?$',
        'instances.shutdown', name="instance-shutdown"),
    url(r'^' + cluster + instance + '/startup/?$',
        'instances.startup', name="instance-startup"),
    url(r'^' + cluster + instance + '/reboot/?$',
        'instances.reboot', name="instance-reboot"),
    #   Orphans
    url(r'^orphans/',
        'general.orphans', name='instance-orphans'),
    
    # Authentication
    url(r'^user/login/?',
        'general.login_view', name="login"),
    url(r'^user/logout/?',
        'general.logout_view', name="logout"),
)

urlpatterns += patterns('ganeti_webmgr.ganeti.organizations',
    # Organizations
    url(r'^organization/(?P<id>\d+)/?$',
        'detail', name="organization-detail"),
    url(r'^organization/(?P<id>\d+)/user/add/?$',
        'add_user', name="organization-add-user"),
    url(r'^organization/(?P<id>\d+)/user/remove/?$',
        'remove_user', name="organization-remove-user"),
    url(r'^organization/(?P<id>\d+)/user/update/?$',
        'update_user', name="organization-update-user"),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
