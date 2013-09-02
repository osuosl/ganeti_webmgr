from clusters.urls import cluster_slug
from django.conf.urls.defaults import patterns, url
from ganetiviz.views import VMJsonView,NodeJsonView,ClusterGraphView,AllClustersView

urlpatterns = patterns(
    'ganetiviz.views',

    url(r'^ganetiviz/vms/%s/$' % cluster_slug, VMJsonView.as_view(), 
        name='json-vms'),

    url(r'^ganetiviz/nodes/%s/$' % cluster_slug, NodeJsonView.as_view(),
        name='json-nodes'),

    url(r'^map/%s/$' % cluster_slug, ClusterGraphView.as_view(), 
        name='cluster-graph'),

    url(r'^maps/$', AllClustersView.as_view(), 
        name='all-clusters-list'),
)
