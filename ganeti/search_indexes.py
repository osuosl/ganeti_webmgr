from haystack.indexes import *
from haystack import site
from ganeti.models import VirtualMachine

class VirtualMachineIndex(RealTimeSearchIndex):
    text = CharField(document=True, use_template=True)

    # We can pull data strait out of the model via `model_attr`
    hostname = CharField(model_attr='hostname')
    
    def get_queryset(self):
        return VirtualMachine.objects.all()
        
site.register(VirtualMachine, VirtualMachineIndex)
