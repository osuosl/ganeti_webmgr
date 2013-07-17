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
from haystack.views import SearchView
from django.contrib.auth.decorators import login_required
import os
from forms.autocomplete_search_form import autocomplete_search_form

from ganeti_web.forms.virtual_machine import vm_wizard
from ganeti_web.views.cluster import (ClusterDetailView, ClusterListView,
                                      ClusterVMListView, ClusterJobListView)
from ganeti_web.views.ganetiviz import VMJsonView,NodeJsonView
from ganeti_web.views.general import AboutView
from ganeti_web.views.jobs import JobDetailView
from ganeti_web.views.node import (NodeDetailView, NodePrimaryListView,
                                   NodeSecondaryListView)
from ganeti_web.views.virtual_machine import VMDeleteView, VMListView
from ganeti_web.views.vm_template import (TemplateFromVMInstanceView,
                                          VMInstanceFromTemplateView,
                                          TemplateListView)

cluster_slug = '(?P<cluster_slug>[-_A-Za-z0-9]+)'
cluster = 'cluster/%s' % cluster_slug

primary_node = 'primary_node/(?P<primary_node>.+)'
secondary_node = 'secondary_node/(?P<secondary_node>.+)'

instance = '(?P<instance>[^/]+)'
host = '(?P<host>[^/]+)'

template = '(?P<template>[^/]+)'

# General
urlpatterns = patterns(
    'ganeti_web.views.general',

    url(r'^$', 'overview', name="index"),

    # Status page
    url(r'^overview/?$', 'overview', name="overview"),
    url(r'^used_resources/?$', 'used_resources', name="used_resources"),

    url(r'^error/clear/(?P<pk>\d+)/?$', 'clear_ganeti_error',
        name="error-clear"),

    url(r'clusters/errors', 'get_errors', name="cluster-errors"),

    url(r'^about/?$', AboutView.as_view(), name="about"),
)


# Users - overridden from users app to use custom templates
urlpatterns += patterns(
    'muddle_users.views.user',
    url(r'^accounts/profile/?', 'user_profile', name='profile',
        kwargs={'template': 'ganeti/users/profile.html'}),
)

# Users
urlpatterns += patterns(
    'ganeti_web.views.users',

    url(r'^user/(?P<user_id>\d+)/key/?$',
        'key_get',
        name="user-key-add"),

    url(r'^keys/get/$', 'key_get', name="key-get"),

    url(r'^keys/get/(?P<key_id>\d+)/?$', 'key_get', name="key-get"),

    url(r'^keys/save/$', 'key_save', name="key-save"),

    url(r'^keys/save/(?P<key_id>\d+)/?$', 'key_save', name="key-save"),

    url(r'^keys/delete/(?P<key_id>\d+)/?$', 'key_delete', name="key-delete"),
)

# All SSH Keys
urlpatterns += patterns(
    'ganeti_web.views.general',
    url(r'^keys/(?P<api_key>\w+)/$', 'ssh_keys', name="key-list"),
)

# Clusters
urlpatterns += patterns(
    'ganeti_web.views.cluster',

    url(r'^clusters/?$', ClusterListView.as_view(), name="cluster-list"),

    url(r'^cluster/add/?$', 'edit', name="cluster-create"),

    url(r'^%s/?$' % cluster, ClusterDetailView.as_view(),
        name="cluster-detail"),

    url(r'^%s/edit/?$' % cluster, 'edit', name="cluster-edit"),

    url(r'^%s/refresh/?$' % cluster, 'refresh', name='cluster-refresh'),

    url(r'^%s/redistribute-config/?$' % cluster, 'redistribute_config',
        name="cluster-redistribute-config"),

    url(r'^%s/users/?$' % cluster, 'users', name="cluster-users"),

    url(r'^%s/virtual_machines/?$' % cluster, ClusterVMListView.as_view(),
        name="cluster-vm-list"),

    url(r'^%s/nodes/?$' % cluster, 'nodes', name="cluster-nodes"),

    url(r'^%s/quota/(?P<user_id>\d+)?/?$' % cluster, 'quota',
        name="cluster-quota"),

    url(r'^%s/permissions/?$' % cluster, 'permissions',
        name="cluster-permissions"),

    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % cluster, 'permissions',
        name="cluster-permissions-user"),

    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % cluster, 'permissions',
        name="cluster-permissions-group"),

    url(r'^(?P<id>\d+)/jobs/status/?$', "job_status",
        name="cluster-job-status"),

    url(r'^%s/keys/(?P<api_key>\w+)/?$' % cluster, "ssh_keys",
        name="cluster-keys"),

    url(r'^%s/object_log/?$' % cluster,
        'object_log',
        name="cluster-object_log"),

    url(r'%s/jobs/?$' % cluster, ClusterJobListView.as_view(),
        name="cluster-job-list"),
)


# Nodes
node_prefix = 'cluster/%s/node/%s' % (cluster_slug, host)
urlpatterns += patterns(
    'ganeti_web.views.node',

    url(r'^%s/?$' % node_prefix, NodeDetailView.as_view(), name="node-detail"),

    url(r'^node/(?P<id>\d+)/jobs/status/?$', "job_status",
        name="node-job-status"),

    url(r'^%s/primary/?$' % node_prefix, NodePrimaryListView.as_view(),
        name="node-primary-vms"),

    url(r'^%s/secondary/?$' % node_prefix, NodeSecondaryListView.as_view(),
        name="node-secondary-vms"),

    url(r'^%s/object_log/?$' % node_prefix, 'object_log',
        name="node-object_log"),

    # Node actions
    url(r'^%s/role/?$' % node_prefix, 'role', name="node-role"),
    url(r'^%s/migrate/?$' % node_prefix, 'migrate', name="node-migrate"),
    url(r'^%s/evacuate/?$' % node_prefix, 'evacuate', name="node-evacuate"),
)

# VM add wizard
urlpatterns += patterns(
    "ganeti_web.forms.virtual_machine",
    url(r"^vm/add/?$",
    vm_wizard(initial_dict={0: {'choices': [u'hostname']}}),
    name="instance-create"),
)

# VirtualMachines
vm_prefix = '%s/%s' % (cluster, instance)
urlpatterns += patterns(
    'ganeti_web.views.virtual_machine',

    url(r'^vms/$', VMListView.as_view(), name="virtualmachine-list"),

    url(r'^%s/?$' % vm_prefix, 'detail', name="instance-detail"),

    url(r'^vm/(?P<id>\d+)/jobs/status/?$', 'job_status',
        name="instance-job-status"),

    url(r'^%s/users/?$' % vm_prefix, 'users', name="vm-users"),

    url(r'^%s/permissions/?$' % vm_prefix, 'permissions',
        name="vm-permissions"),

    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % vm_prefix, 'permissions',
        name="vm-permissions-user"),

    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % vm_prefix,
        'permissions', name="vm-permissions-user"),

    url(r'^%s/vnc/?$' % vm_prefix, 'novnc', name="instance-vnc"),

    url(r'^%s/vnc/popout/?$' % vm_prefix, 'novnc',
        {'template': 'ganeti/virtual_machine/vnc_popout.html'},
        name="instance-vnc-popout"),

    url(r'^%s/vnc_proxy/?$' % vm_prefix, 'vnc_proxy',
        name="instance-vnc-proxy"),

    url(r'^%s/shutdown/?$' % vm_prefix, 'shutdown', name="instance-shutdown"),

    url(r'^%s/shutdown-now/?$' % vm_prefix, 'shutdown_now',
        name="instance-shutdown-now"),

    url(r'^%s/startup/?$' % vm_prefix, 'startup', name="instance-startup"),

    url(r'^%s/reboot/?$' % vm_prefix, 'reboot', name="instance-reboot"),

    url(r'^%s/migrate/?$' % vm_prefix, 'migrate', name="instance-migrate"),

    url(r'^%s/replace_disks/?$' % vm_prefix, 'replace_disks',
        name="instance-replace-disks"),

    url(r"^%s/delete/?$" % vm_prefix, VMDeleteView.as_view(),
        name="instance-delete"),

    url(r"^%s/reinstall/?$" % vm_prefix, "reinstall",
        name="instance-reinstall"),

    url(r"^%s/edit/?$" % vm_prefix, "modify", name="instance-modify"),

    url(r'^%s/edit/confirm/?$' % vm_prefix, "modify_confirm",
        name="instance-modify-confirm"),

    url(r"^%s/rename/?$" % vm_prefix, "rename", name="instance-rename"),

    url(r"^%s/reparent/?$" % vm_prefix, "reparent", name="instance-reparent"),

    url(r'^%s/keys/(?P<api_key>\w+)/?$' % vm_prefix, "ssh_keys",
        name="instance-keys"),

    url(r'^%s/object_log/?$' % vm_prefix, 'object_log', name="vm-object_log"),
)

# VirtualMachineTemplates
template_prefix = '%s/template/%s' % (cluster, template)
urlpatterns += patterns(
    'ganeti_web.views.vm_template',

    url(r'^templates/$', TemplateListView.as_view(), name='template-list'),

    url(r'^template/create/$',
        vm_wizard(initial_dict={0: {'choices': [u'template_name']}}),
        name='template-create'),

    url(r'^%s/?$' % template_prefix, 'detail', name='template-detail'),

    url(r'^%s/delete/?$' % template_prefix, 'delete', name='template-delete'),

    url(r'^%s/edit/?$' % template_prefix, vm_wizard(), name='template-edit'),

    url(r'^%s/copy/?$' % template_prefix, 'copy', name='template-copy'),

    url(r'^%s/vm/?$' % template_prefix, VMInstanceFromTemplateView.as_view(),
        name='instance-create-from-template'),

    url(r'^%s/template/?$' % vm_prefix, TemplateFromVMInstanceView.as_view(),
        name='template-create-from-instance'),
)

# Virtual Machine Importing
urlpatterns += patterns(
    'ganeti_web.views.importing',

    url(r'^import/orphans/', 'orphans',
        name='import-orphans'),
    url(r'^import/missing/', 'missing_ganeti',
        name='import-missing'),
    url(r'^import/missing_db/', 'missing_db',
        name='import-missing_db'),
)

# Node Importing
urlpatterns += patterns(
    'ganeti_web.views.importing_nodes',

    url(r'^import/node/missing/', 'missing_ganeti',
        name='import-nodes-missing'),

    url(r'^import/node/missing_db/', 'missing_db',
        name='import-nodes-missing_db'),
)

# Jobs
job = '%s/job/(?P<job_id>\d+)' % cluster
urlpatterns += patterns(
    'ganeti_web.views.jobs',

    url(r'^%s/status/?' % job, 'status', name='job-status'),

    url(r'^%s/clear/?' % job, 'clear', name='job-clear'),

    url(r'^%s/?' % job, JobDetailView.as_view(), name='job-detail'),
)

# Search
urlpatterns += patterns(
    'ganeti_web.views.search',

    url(r'^search/suggestions.json', 'suggestions', name='search-suggestions'),

    url(r'^search/detail_lookup', 'detail_lookup', name='search-detail-lookup')
)

urlpatterns += patterns(
    'ganeti_web.views.user_search',

    url(r'^search/owners/?$', 'search_owners', name="owner-search")
)

urlpatterns += patterns(
    'haystack.views',
    url(r'^search/',
        login_required(SearchView(form_class=autocomplete_search_form)),
        name='search')
)

# Ganetiviz
urlpatterns += patterns(
    'ganeti_web.views.graph',

    url(r'^ganetiviz/vms/(?P<cluster_hostname>[\.\w]+)$', VMJsonView.as_view(), 
        name='json-vms'),

    url(r'^ganetiviz/nodes/(?P<cluster_hostname>[\.\w]+)$', NodeJsonView.as_view(),
        name='json-nodes'),
)

# The following is used to serve up local static files like images
root = '%s/static' % os.path.dirname(os.path.realpath(__file__))
urlpatterns += patterns(
    '',
    (r'^static/(?P<path>.*)',
    'django.views.static.serve',
    {'document_root': root})
)
