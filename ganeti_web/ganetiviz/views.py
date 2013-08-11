from django.conf import settings
from django.core import serializers
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.views.generic import DetailView,TemplateView,View

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
        selected_fields = ('hostname','primary_node','secondary_node','status')
        vm_json_data = serializers.serialize('json', vm_queryset, fields=selected_fields, use_natural_keys=True)

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
        selected_fields = ('hostname','ram_total','ram_free','offline','role')
        node_json_data = serializers.serialize('json', node_queryset, fields= selected_fields)

        return HttpResponse(node_json_data, content_type='application/json')  


class ClusterGraphView(TemplateView):
    """
    View that dispatches the appropriate template file responsible for visual
    mapping of the Cluster Graph.
    """
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(ClusterGraphView, self).get_context_data(**kwargs)
        cluster_hostname=self.kwargs['cluster_hostname']
        cluster_obj = Cluster.objects.get(hostname=cluster_hostname)
        cluster_slug = cluster_obj.slug
        context['cluster_hostname'] = cluster_hostname
        context['cluster_slug'] = cluster_slug
        return context

