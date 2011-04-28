from haystack import indexes
from haystack import site
from ganeti.models import VirtualMachine

class VirtualMachineIndex(indexes.RealTimeSearchIndex):
    text = indexes.CharField(document=True, use_template=True)

    # We can pull data strait out of the model via `model_attr`
    hostname = indexes.CharField(model_attr='hostname')
    
    # Experimenting with auto-complete
    content_auto = indexes.EdgeNgramField(model_attr='hostname')

    def get_queryset(self):
        return VirtualMachine.objects.all()

site.register(VirtualMachine, VirtualMachineIndex)
