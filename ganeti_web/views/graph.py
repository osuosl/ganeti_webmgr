from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.generic import TemplateView

from ganeti_web.models import Cluster, Node, VirtualMachine
from ganeti_web.views.generic import LoginRequiredMixin



def vmqs_to_dicts(vm_queryset,node_queryset):
    '''
    (Virtual Machine Queryset to Dictionaries)
    A function that converts a queryset of virtual machines belonging to a cluster to relevant structures.
    The structures returned are:
     #nodedict - A dictionary mapping a primary node to all of its dependent instances (primary instances)
     #psdict -   A dictionary mapping an "instance group" (primary_node) to a dictionary of secondary nodes having weights.
                 Example : node1:{node3 : 5} => Implies that 5 instances having node1 as primary have node3 as secondary.
    '''
    nodedict = {}
    psdict = {}
    for node in node_queryset:
        nodedict[node] = []
        psdict[node] = {}

    for vm_obj in vm_queryset:
        vm = vm_obj.hostname
        pnode = vm_obj.primary_node
        snode = vm_obj.secondary_node
        ##Creating the PrimaryNode-Instance relations.
        try:
            nodedict[pnode]
            nodedict[pnode].append(vm)
        except KeyError:
            nodedict[pnode] = [vm,]

        ##Creating the "instance-group" to secondary node relations.
        try:
            # pnode might not be already there in psdict, thats why we "try" it.
            snodes = psdict[pnode]
            # Increase count of no. of links from pnode to the respective snode.
            if snode in snodes:
                snodes[snode] += 1
            else:
                if snode != 'None':
                    snodes[snode] = 1
        #This exception occurs only when pnode not in psdict.
        except KeyError:
            if snode != 'None':
                psdict[pnode] = {snode: 1}
    return (nodedict,psdict,)


def js_nodes_obj(nodedict):
    '''
    Takes in a "nodedict" and converts it into a Javascript Nodes object.
    '''
    s = '{\n'
    for node in sorted(nodedict.keys()):
        s += '"%s":{color:CLR.ganetinode, shape:"dot", alpha:1},\n'%(node,)
        for instance in nodedict[node]:
            s += '"%s":{color:CLR.ganetivm, alpha:0},\n'%(instance,)
        s += '}\n'
    return s


def js_edges_obj(nodedict,psdict):
    '''
    Takes in "nodedict" and "psdict" dictionaries and uses it to 
    generate a string representation of the Javascript EDGE object.
    '''
    s = '{\n'
    for node in sorted(nodedict.keys()):
        s += '\t"%s":{\n'%(node,)

        #Edges to Instances.
        for instance in nodedict[node]:
            s += '\t\t"%s":{length:6},\n'%(instance,)

        #Edges to Secondary Nodes.
        for snode,slinkweight in psdict[node].items():
            if snode:
                s += '\t\t"%s":{length:15, width:%d},\n'%(snode,slinkweight)
        s+='\t},\n'
    s+='}'
    return s


class ClusterGraphView(LoginRequiredMixin, TemplateView):
    """
    View for generating a graph representing a Ganeti Cluster.
    """
    template_name = "graph/graph_object.js"
    #cluster_hostname = "ganeti.example.org"

    def get_context_data(self, **kwargs):
        context = super(ClusterGraphView, self).get_context_data(** kwargs)

        cluster = Cluster.objects.get(slug=self.request.GET['cluster'])
        nodeqs = Node.objects.filter(cluster=cluster)
        vmqs = VirtualMachine.objects.filter(cluster=cluster)
        nodedict,psdict = vmqs_to_dicts(vmqs,nodeqs)

        graph_nodes = js_nodes_obj(nodedict)
        graph_edges = js_edges_obj(nodedict,psdict)

        context['graph_nodes'] = graph_nodes
        context['graph_edges'] = graph_edges
        return context

