from django.conf.urls.defaults import patterns, url
from clusters.views import (ClusterDetailView, ClusterListView,
                            ClusterVMListView, ClusterJobListView)

cluster_slug = '(?P<cluster_slug>[-_A-Za-z0-9]+)'
cluster = 'cluster/%s' % cluster_slug

urlpatterns = patterns(
    'clusters.views',

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
