from ganeti_webmgr.clusters.urls import cluster_slug
from django.conf.urls.defaults import patterns, url
from ganeti_webmgr.ganetiviz.views import ClusterGraphView, AllClustersView,\
    ClusterJsonView, InstanceExtraDataView

# Care must be taken to allow dots to be captured in any hostname.
instance_hostname = '(?P<instance_hostname>[^/]+)'

urlpatterns = patterns(
    'ganetiviz.views',

    url(r'^ganetiviz/cluster/%s/$' % cluster_slug, ClusterJsonView.as_view(),
        name='json-cluster'),

    url(r'^ganetiviz/%s/%s/$' % (cluster_slug, instance_hostname),
        InstanceExtraDataView.as_view(), name='instance-info'),

    url(r'^map/%s/$' % cluster_slug, ClusterGraphView.as_view(),
        name='cluster-graph'),

    url(r'^maps/$', AllClustersView.as_view(),
        name='all-clusters-list'),
)
