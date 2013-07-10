from django.conf import settings
from django.core import serializers
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.views.generic import DetailView

from ganeti_web.models import Cluster, Node, VirtualMachine
from ganeti_web.views.generic import LoginRequiredMixin


class VMJsonView(DetailView):
    """
    View for generating JSON representation of Virtual Machines in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/vms/ganeti.example.org"
    """
    def get(self, request, *args, **kwargs):
        #cluster_hostname = "ganeti.example.org"
        cluster_hostname=self.kwargs['cluster_hostname']

        cluster = Cluster.objects.get(hostname=cluster_hostname)
        vm_queryset = VirtualMachine.objects.filter(cluster=cluster)
        vm_json_data = serializers.serialize('json', vm_queryset, fields=('hostname','primary_node','secondary_node'), use_natural_keys=True)

        return HttpResponse(vm_json_data, content_type='application/json')  


class NodeJsonView(DetailView):
    """
    View for generating JSON representation of Nodes in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/vms/ganeti.example.org"
    """
    def get(self, request, *args, **kwargs):
        #cluster_hostname = "ganeti.example.org"
        cluster_hostname=self.kwargs['cluster_hostname']

        cluster = Cluster.objects.get(hostname=cluster_hostname)
        node_queryset = Node.objects.filter(cluster=cluster)
        node_json_data = serializers.serialize('json', node_queryset, fields=('hostname','ram_total','ram_free'))

        return HttpResponse(node_json_data, content_type='application/json')  

