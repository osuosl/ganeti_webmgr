from django.conf.urls.defaults import patterns, url
from ganetiviz.views import VMJsonView,NodeJsonView

urlpatterns += patterns(
    'ganetiviz.views',

    url(r'^ganetiviz/vms/(?P<cluster_hostname>[\.\w]+)$', VMJsonView.as_view(), 
        name='json-vms'),

    url(r'^ganetiviz/nodes/(?P<cluster_hostname>[\.\w]+)$', NodeJsonView.as_view(),
        name='json-nodes'),

    url(r'^map/(?P<cluster_hostname>[\.\w]+)$', ClusterGraphView.as_view(), 
        name='cluster-graph'),
)
