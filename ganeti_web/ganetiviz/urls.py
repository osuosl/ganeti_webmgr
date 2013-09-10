from clusters.urls import cluster_slug
from django.conf.urls.defaults import patterns, url
from ganetiviz.views import VMJsonView,NodeJsonView,ClusterGraphView, \
                            AllClustersView,ClusterJsonView,\
                            InstanceExtraDataView

validfqdnregex = "(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])"

instance_hostname = '(?P<instance_hostname>%s)'%(validfqdnregex,)


urlpatterns = patterns(
    'ganetiviz.views',

    url(r'^ganetiviz/cluster/%s/$' % cluster_slug, ClusterJsonView.as_view(),
        name='json-cluster'),

    url(r'^ganetiviz/vms/%s/$' % cluster_slug, VMJsonView.as_view(),
        name='json-vms'),

    url(r'^ganetiviz/nodes/%s/$' % cluster_slug, NodeJsonView.as_view(),
        name='json-nodes'),

    url(r'^ganetiviz/%s/%s/$' % (cluster_slug,instance_hostname),
        InstanceExtraDataView.as_view(), name='instance-info'),

    url(r'^map/%s/$' % cluster_slug, ClusterGraphView.as_view(),
        name='cluster-graph'),

    url(r'^maps/$', AllClustersView.as_view(),
        name='all-clusters-list'),

)
