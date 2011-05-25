from haystack.indexes import *
from haystack import site
from ganeti.models import VirtualMachine, Cluster, Node

''' Haystack search indexex.

This is where the search indexes are defined. They fill the Haystack search 
query set (the set of objects that are searchable.) There should be one index 
defined per GWM model.

Note that I'm using `RealTimeSearchIndex` to index the GWM models every time
it changes. This keeps things up-to-date at the cost of some performance. If
you're experienceing db performance issues, try using `SearchIndex` instead and
run `./manage.py update_index` every half-hour or so. (For more information,
see 
http://docs.haystacksearch.org/dev/searchindex_api.html#keeping-the-index-fresh
)
'''

class VirtualMachineIndex(RealTimeSearchIndex):
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

class ClusterIndex(RealTimeSearchIndex):
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
        return Cluster.objects.all()

site.register(Node, NodeIndex)
