from haystack import site
from haystack.indexes import *
from virtualmachines.models import VirtualMachine
from clusters.models import Cluster
from nodes.models import Node

''' Haystack search indexex.

This is where the search indexes are defined. They fill the Haystack search
query set (the set of objects that are searchable.) There should be one index
defined per GWM model.

Note that we're using the `SearchIndex` update-based search indexer. This means
the search index will need to be updated periodically with
`./manage.py update_index`

Previously, we were using `RealTimeSearchIndex` which updated the index anytime
an associated GWM model changed in the database. Concerns about database
performance, database locking issues, and dev server socket problems pushed us
away from this indexer.

For more informaiton about the availible search indexers, see
http://docs.haystacksearch.org/dev/searchindex_api.html#keeping-the-index-fresh
'''


class VirtualMachineIndex(SearchIndex):
    ''' Search index for VirtualMachines '''

    text = CharField(document=True, use_template=True)

    # We can pull data strait out of the model via `model_attr`
    # (Commmenting out 'cause I'm not sure it's needed)
    # hostname = CharField(model_attr='hostname')

    # Autocomplete search field on the `hostname` model field
    content_auto = EdgeNgramField(model_attr='hostname')

    def get_queryset(self):
        return VirtualMachine.objects.all()

site.register(VirtualMachine, VirtualMachineIndex)


class ClusterIndex(SearchIndex):
    ''' Search index for Clusters '''

    text = CharField(document=True, use_template=True)

    # Autocomplete search field on `hostname` model field
    content_auto = EdgeNgramField(model_attr='hostname')

    def get_queryset(self):
        return Cluster.objects.all()

site.register(Cluster, ClusterIndex)


class NodeIndex(RealTimeSearchIndex):
    ''' Search index for Nodes '''

    text = CharField(document=True, use_template=True)

    # Autocomplete search field on `hostname` model field
    content_auto = EdgeNgramField(model_attr='hostname')

    def get_queryset(self):
        return Node.objects.all()

site.register(Node, NodeIndex)
