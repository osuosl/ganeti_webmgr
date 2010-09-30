from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list, object_detail
from ganeti_webmgr.ganeti.models import *

urlpatterns = patterns('ganeti_webmgr.ganeti.views',
    # Example:
    # (r'^ganeti_webmgr/', include('ganeti_webmgr.foo.urls')),
    url(r'^/?$',
        'index', name="cluster-overview"),
        
    # Cluster
    #   List
    url(r'^clusters/',
        'cluster_list', name="cluster-list"),
    #   Detail
    url(r'^cluster/(?P<cluster_slug>\w+)/?$',
        'cluster_detail', name="cluster-detail"),
    # Instance
    #  List
    #  Detail
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/?',
        'instance', name="instance-detail"),
    #  Create
    url(r'^cluster/(?P<cluster_slug>\w+)/create/?$',
        'create', name="instance-create"),
    #  Start, Stop, Reboot
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/vnc/?$',
        'vnc', name="instance-vnc"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/shutdown/?$',
        'shutdown', name="instance-shutdown"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/startup/?$',
        'startup', name="instance-startup"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/reboot/?$',
        'reboot', name="instance-reboot"),
    #   Orphans
    url(r'^orphans/',
        'orphans', name='instance-orphans'),
    
    # Authentication
    url(r'^user/login/?',
        'login_view', name="login"),
    url(r'^user/logout/?',
        'logout_view', name="logout"),
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
