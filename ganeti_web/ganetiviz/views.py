from django.conf import settings
from django.core import serializers
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.views.generic import DetailView,TemplateView,View

from ganeti_web.models import Cluster, Node, VirtualMachine
from ganeti_web.views.generic import LoginRequiredMixin
import simplejson as json
from utils import get_rapi


class ClusterJsonView(LoginRequiredMixin,DetailView):
    """
    View for generating JSON representation of the data in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/cluster/ganeti"
    """
    def get(self, request, *args, **kwargs):
        cluster_slug=self.kwargs['cluster_slug']

        cluster = Cluster.objects.select_related("node","virtualmachine").get(slug=cluster_slug)
        vms = cluster.virtual_machines.all()
        nodes = cluster.nodes.all()

        # .values() method does not return actual list but list like django object. 
        # Imp. to convert to lists for making it JSON Serializable
        vms = list(vms.values('hostname','primary_node__hostname',
                              'secondary_node__hostname','status','owner',))
        nodes = list(nodes.values('hostname','ram_total','ram_free','offline','role'))

        cluster_data = { 'nodes' : nodes, 'vms' : vms }
        cluster_json = json.dumps(cluster_data)

        return HttpResponse(cluster_json, content_type='application/json')  


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


class InstanceExtraDataView(LoginRequiredMixin,DetailView):
    """
    View for returning additional instance information (useful) for a particular
    instance in a cluster via ganeti RAPI  python client.
    """
    def get(self, request, *args, **kwargs):
        cluster_slug=self.kwargs['cluster_slug']
        instance_hostname=self.kwargs['instance_hostname']

        #cluster = Cluster.objects.get(slug=cluster_slug) # Changed to next line for query optimization.
        cluster = Cluster.objects.get(slug=cluster_slug)

        r = get_rapi(cluster.hash,cluster.cluster_id)

        selected_fields = ('beparams','nic.bridges','network_port','status','os')

        # Blocking request to Ganeti RAPI to return instance info.
        instance_info = r.GetInstance(instance_hostname)

        useful_instance_info = dict((useful_key, instance_info[useful_key])
                                    for useful_key in selected_fields )
        instance_info_json = json.dumps(useful_instance_info)

        return HttpResponse(instance_info_json, content_type='application/json')


'''

# Not being used now, but still kept as it might be useful again in future.
class VMJsonView(LoginRequiredMixin,DetailView):
    """
    View for generating JSON representation of Virtual Machines in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/vms/ganeti"
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
        vm_json_data = serializers.serialize('json', vms, 
                                             fields=selected_fields, 
                                             use_natural_keys=True)

        return HttpResponse(vm_json_data, content_type='application/json')  


# Not being used now, but still kept as it might be useful again in future.
class NodeJsonView(LoginRequiredMixin,DetailView):
    """
    View for generating JSON representation of Nodes in a Cluster (Cluster-Graph)
    The cluster is specified in the url, example: "/ganetiviz/vms/ganeti"
    """
    def get(self, request, *args, **kwargs):
        #cluster_slug = "ganeti"
        cluster_slug=self.kwargs['cluster_slug']

        cluster = Cluster.objects.select_related("node").get(slug=cluster_slug)
        node_queryset = cluster.nodes.all()
        selected_fields = ('hostname','ram_total','ram_free','offline','role')
        node_json_data = serializers.serialize('json', node_queryset, fields= selected_fields)

        return HttpResponse(node_json_data, content_type='application/json')  
'''
