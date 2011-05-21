from haystack.indexes import *
from haystack import site
from ganeti.models import VirtualMachine, Cluster

''' Haystack search indexex.

This is where the indexes are defined. They fill the Haystack search query set
(the set of objects that are searchable.) There should be one index defined per
GWM object.
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
