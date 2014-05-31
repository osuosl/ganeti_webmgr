from django.conf.urls.defaults import patterns, url
from .views import NodeDetailView, NodePrimaryListView, NodeSecondaryListView

from ganeti_webmgr.clusters.urls import cluster_slug
host = '(?P<host>[^/]+)'
node_prefix = 'cluster/%s/node/%s' % (cluster_slug, host)

urlpatterns = patterns(
    'nodes.views',

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
