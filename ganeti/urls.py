from django.conf.urls.defaults import *

cluster = 'cluster/(?P<cluster_slug>\w+)'
instance = '/(?P<instance>[^/]+)'

urlpatterns = patterns('ganeti.views.general',
    url(r'^$', 'index', name="cluster-overview"),
    #   Orphans
    url(r'^orphans/','orphans', name='instance-orphans'),
    # Authentication
    url(r'^accounts/profile/?', 'user_profile', name="profile"),
)

# Clusters
urlpatterns += patterns('ganeti.views.cluster',
    #   List
    url(r'^clusters/$', 'list_', name="cluster-list"),
    #   Add
    url(r'^cluster/add/?$', 'edit', name="cluster-create"),
    #   Detail
    url(r'^%s/?$' % cluster, 'detail', name="cluster-detail"),
    #   Edit
    url(r'^%s/edit/?$' % cluster, 'edit', name="cluster-edit"),
    #   Delete
    url(r'^%s/delete/?$' % cluster, 'delete', name="cluster-delete"),
    #   User
    url(r'^%s/users/?$' % cluster, 'users', name="cluster-users"),
    url(r'^%s/virtual_machines/?$' % cluster, 'virtual_machines', name="cluster-vms"),
    url(r'^%s/nodes/?$' % cluster, 'nodes', name="cluster-nodes"),
    url(r'^%s/quota/(?P<user_id>\d+)?/?$'% cluster, 'quota', name="cluster-quota"),
    url(r'^%s/permissions/?$' % cluster, 'permissions', name="cluster-permissions"),
    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % cluster, 'permissions', name="cluster-permissions-user"),
    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % cluster, 'permissions', name="cluster-permissions-group"),
)


# VirtualMachines
vm_prefix = '%s%s' %  (cluster, instance)
urlpatterns += patterns('ganeti.views.virtual_machine',
    #  List
    url(r'^vms/$', 'list_', name="virtualmachine-list"),
    #  Create
    url(r'^vm/add/$', 'create', name="instance-create"),
    url(r'^vm/add/(?P<cluster_slug>\w+)$', 'create', name="instance-create"),
    
    #  Detail
    url(r'^%s/?$' % vm_prefix, 'detail', name="instance-detail"),
    url(r'^%s/users/?$' % vm_prefix, 'users', name="vm-users"),
    url(r'^%s/permissions/?$' % vm_prefix, 'permissions', name="vm-permissions"),
    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % vm_prefix, 'permissions', name="vm-permissions-user"),
    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % vm_prefix, 'permissions', name="vm-permissions-user"),
    
    #  Start, Stop, Reboot
    url(r'^%s/vnc/?$' % vm_prefix, 'vnc', name="instance-vnc"),
    url(r'^%s/shutdown/?$' % vm_prefix, 'shutdown', name="instance-shutdown"),
    url(r'^%s/startup/?$' % vm_prefix, 'startup', name="instance-startup"),
    url(r'^%s/reboot/?$' % vm_prefix, 'reboot', name="instance-reboot"),
)