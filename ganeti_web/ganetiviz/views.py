from django.conf import settings
from django.core import serializers
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.views.generic import DetailView,TemplateView,View

from ganeti_web.models import Cluster, Node, VirtualMachine
from ganeti_web.views.generic import LoginRequiredMixin

import timeit


class VMJsonView(LoginRequiredMixin,DetailView):
    """
    View for generating JSON representation of Virtual Machines in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/vms/ganeti.example.org"
    """
    def get(self, request, *args, **kwargs):
        #cluster_slug = "ganeti"
        cluster_slug=self.kwargs['cluster_slug']

        #cluster = Cluster.objects.get(slug=cluster_slug) # Changed to next line for query optimization.
        cluster = Cluster.objects.select_related("virtualmachine").get(slug=cluster_slug)

        #vm_queryset = VirtualMachine.objects.filter(cluster=cluster)
        vms = cluster.virtual_machines.all()

        selected_fields = ('hostname','primary_node','secondary_node','status',
                           'owner','operating_system','ram','minram')
        vm_json_data = serializers.serialize('json', vms, fields=selected_fields, use_natural_keys=True)

        return HttpResponse(vm_json_data, content_type='application/json')  


class NodeJsonView(LoginRequiredMixin,DetailView):
    """
    View for generating JSON representation of Nodes in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/vms/ganeti.example.org"
    """
    def get(self, request, *args, **kwargs):
        #cluster_slug = "ganeti"
        cluster_slug=self.kwargs['cluster_slug']

        cluster = Cluster.objects.select_related("node").get(slug=cluster_slug)
        node_queryset = cluster.nodes.all()
        selected_fields = ('hostname','ram_total','ram_free','offline','role')
        node_json_data = serializers.serialize('json', node_queryset, fields= selected_fields)

        return HttpResponse(node_json_data, content_type='application/json')  


class ClusterGraphView(LoginRequiredMixin,TemplateView):
    """
    View that dispatches the appropriate template file responsible for visual
    mapping of the Cluster Graph.
    """
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(ClusterGraphView, self).get_context_data(**kwargs)

        cluster_slug=self.kwargs['cluster_slug']
        cluster = Cluster.objects.get(slug=cluster_slug)
        context['cluster_slug'] = cluster_slug

        return context


class AllClustersView(LoginRequiredMixin,TemplateView):
    """
    View that renders a template with showing a list of available clusters 
    each linking to its corresponding Map Page.
    """
    template_name = 'cluster-list.html'

    def get_context_data(self, **kwargs):
        context = super(AllClustersView, self).get_context_data(**kwargs)

        clusters = Cluster.objects.all()
        context['clusters'] = clusters

        return context

