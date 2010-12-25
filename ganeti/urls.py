# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.conf.urls.defaults import patterns, url

cluster_slug = '(?P<cluster_slug>[-_A-Za-z0-9]+)'
cluster = 'cluster/%s' % cluster_slug
instance = '/(?P<instance>[^/]+)'

# Users
urlpatterns = patterns('ganeti.views.users',
    url(r'^accounts/profile/?', 'user_profile', name="profile"),
    url(r'^users/?$', 'user_list', name="user-list"),
    url(r'^users/add$', 'user_add', name="user-create"),
    url(r'^user/(?P<user_id>\d+)/edit/?$', 'user_edit', name="user-edit"),
    url(r'^user/(?P<user_id>\d+)/password/?$', 'user_password', name="user-password"),

    # ssh keys
    url(r'^keys/get/$',                     'key_get', name="key-get"),
    url(r'^keys/get/(?P<key_id>\d+)/?$',    'key_get', name="key-get"),
    url(r'^keys/save/$',                    'key_save', name="key-save"),
    url(r'^keys/save/(?P<key_id>\d+)/?$',   'key_save', name="key-save"),
    url(r'^keys/delete/(?P<key_id>\d+)/?$', 'key_delete', name="key-delete"),
)

# Clusters
urlpatterns += patterns('ganeti.views.cluster',
    url(r'^$', 'list_', name="cluster-overview"),
    #   List
    url(r'^clusters/$', 'list_', name="cluster-list"),
    #   Add
    url(r'^cluster/add/?$', 'edit', name="cluster-create"),
    #   Detail
    url(r'^%s/?$' % cluster, 'detail', name="cluster-detail"),
    #   Edit
    url(r'^%s/edit/?$' % cluster, 'edit', name="cluster-edit"),
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
    url(r'^vm/add/?$', 'create', name="instance-create"),
    url(r'^vm/add/choices/$', 'cluster_choices', name="instance-create-cluster-choices"),
    url(r'^vm/add/options/$', 'cluster_options', name="instance-create-cluster-options"),
    url(r'^vm/add/defaults/$', 'cluster_defaults', name="instance-create-cluster-defaults"),
    url(r'^vm/add/%s/?$' % cluster_slug, 'create', name="instance-create"),
    
    #  Detail
    url(r'^%s/?$' % vm_prefix, 'detail', name="instance-detail"),
    url(r'^%s/users/?$' % vm_prefix, 'users', name="vm-users"),
    url(r'^%s/permissions/?$' % vm_prefix, 'permissions', name="vm-permissions"),
    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % vm_prefix, 'permissions', name="vm-permissions-user"),
    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % vm_prefix, 'permissions', name="vm-permissions-user"),
    
    #  Start, Stop, Reboot, VNC
    url(r'^%s/vnc/?$' % vm_prefix, 'vnc', name="instance-vnc"),
    url(r'^vm/vnc_proxy/(?P<target_host>[^/]+)/(?P<target_port>\d+)/?$', 'vnc_proxy', name="vm-vnc-proxy"),
    url(r'^%s/shutdown/?$' % vm_prefix, 'shutdown', name="instance-shutdown"),
    url(r'^%s/startup/?$' % vm_prefix, 'startup', name="instance-startup"),
    url(r'^%s/reboot/?$' % vm_prefix, 'reboot', name="instance-reboot"),

    # Delete
    url(r"^%s/delete/?$" % vm_prefix, "delete", name="instance-delete"),

    # SSH Keys
    url(r'^%s/keys/(?P<api_key>\w+)/?$' % vm_prefix, "ssh_keys", name="instance-keys"),
)


# Virtual Machine Importing
urlpatterns += patterns('ganeti.views.importing',
    url(r'^import/orphans/', 'orphans', name='import-orphans'),
    url(r'^import/missing/', 'missing_ganeti', name='import-missing'),
    url(r'^import/missing_db/', 'missing_db', name='import-missing_db'),
)

# Jobs
urlpatterns += patterns('ganeti.views.jobs',
    url(r'^%s/job/(?P<job_id>\d+)/status' % cluster, 'status', name='job-status'),
)
