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
    url(r'^accounts/profile/?', 'user_profile', name="profile"),
)

# Clusters
urlpatterns += patterns('ganeti_webmgr.ganeti.views.cluster',
    #   List
    url(r'^clusters/$', 'list', name="cluster-list"),
    #   Add
    url(r'^cluster/add/?$', 'add', name="cluster-create"),
    #   Detail
    url(r'^%s/?$' % cluster, 'detail', name="cluster-detail"),
    #   Edit
    url(r'^%s/edit/?$' % cluster, 'edit', name="cluster-edit"),
    #   User
    url(r'^%s/users/?$' % cluster, 'cluster_users', name="cluster-users"),
    url(r'^%s/virtual_machines/?$' % cluster, 'virtual_machines', name="cluster-vms"),
    url(r'^%s/nodes/?$' % cluster, 'nodes', name="cluster-nodes"),
    url(r'^%s/quota/(?P<user_id>\d+)?/?$'% cluster, 'quota', name="cluster-quota"),
    url(r'^%s/permissions/?$' % cluster, 'permissions', name="cluster-permissions"),
    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % cluster, 'permissions', name="foo"),
    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % cluster, 'permissions', name="cluster-permissions-group"),
)

# Instances
prefix = '%s%s' %  (cluster, instance)
urlpatterns += patterns('ganeti_webmgr.ganeti.views.virtual_machine',
    #  List
    url(r'^vms/$', 'list', name="virtualmachine-list"),
    #  Create
    url(r'^vm/add/$', 'create', name="instance-create"),
    url(r'^vm/add/(?P<cluster_slug>\w+)$', 'create', name="instance-create"),
    #  Detail
    url(r'^%s/?$' % prefix, 'detail', name="instance-detail"),
    #  Start, Stop, Reboot
    url(r'^%s/vnc/?$' % prefix, 'vnc', name="instance-vnc"),
    url(r'^%s/shutdown/?$' % prefix, 'shutdown', name="instance-shutdown"),
    url(r'^%s/startup/?$' % prefix, 'startup', name="instance-startup"),
    url(r'^%s/reboot/?$' % prefix, 'reboot', name="instance-reboot"),
)