# Copyright (C) 2010 Oregon State University et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext as _

from ganeti_web.forms.importing import NodeForm
from ganeti_web.middleware import Http403
from ganeti_web.models import Cluster, Node, VirtualMachine


@login_required
def importing(request):
    """
    View that loads main importing view
    """
    user = request.user
    if not user.is_superuser or user.get_objects_any_perms(Cluster, ['admin']):
        raise Http403(_('You do not have sufficient privileges'))

    return render_to_response('ganeti/importing/nodes/main.html',
              context_instance=RequestContext(request))


@login_required
def missing_ganeti(request):
    """
    View for displaying VirtualMachines missing from the ganeti cluster
    """
    user = request.user
    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_any_perms(Cluster, ['admin'])
        if not clusters:
            raise Http403(_('You do not have sufficient privileges'))

    nodes = []
    for cluster in clusters:
        for node in cluster.nodes_missing_in_ganeti:
            nodes.append((node, node))

    if request.method == 'POST':
        # process updates if this was a form submission
        form = NodeForm(nodes, request.POST)
        if form.is_valid():
            # update all selected Nodes
            data = form.cleaned_data
            node_ids = data['nodes']
            Node.objects.filter(hostname__in=node_ids).delete()

    else:
        form = NodeForm(nodes)

    nodes = {}
    for cluster in clusters:
        for node in cluster.nodes_missing_in_ganeti:
            nodes[node] = (cluster.hostname, node)

    node_hostnames = nodes.keys()
    node_hostnames.sort()

    node_tuple_list = []
    for i in node_hostnames:
        node_tuple_list.append((i, nodes[i][0], nodes[i][1]))

    nodes = node_tuple_list

    return render_to_response("ganeti/importing/nodes/missing.html"
                              , {
        'nodes': nodes,
        'form':form,
        },
        context_instance=RequestContext(request),
    )


@login_required
def missing_db(request):
    """
    View for displaying Nodes missing from the database
    """
    user = request.user
    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_any_perms(Cluster, ['admin'])
        if not clusters:
            raise Http403(_('You do not have sufficient privileges'))

    nodes = []
    for cluster in clusters:
        for hostname in cluster.nodes_missing_in_db:
            nodes.append(('%s:%s' % (cluster.id, hostname), hostname))

    if request.method == 'POST':
        # process updates if this was a form submission
        form = NodeForm(nodes, request.POST)

        if form.is_valid():
            # update all selected Nodes
            data = form.cleaned_data
            node_ids = data['nodes']

            # create missing Nodes
            for node in node_ids:
                cluster_id, host = node.split(':')
                cluster = Cluster.objects.get(id=cluster_id)
                node = Node.objects.create(hostname=host, cluster=cluster)
                node.refresh()

                # refresh all vms on this node
                VirtualMachine.objects\
                    .filter(cluster=cluster, hostname__in=node.info['pinst_list']) \
                    .update(primary_node=node)

                VirtualMachine.objects\
                    .filter(cluster=cluster, hostname__in=node.info['sinst_list']) \
                    .update(secondary_node=node)

    else:
        form = NodeForm(nodes)

    nodes = {}
    for cluster in clusters:
        for hostname in cluster.nodes_missing_in_db:
            nodes[hostname] = ('%s:%s' % (cluster.id, hostname), cluster.hostname, hostname)
    node_hostnames = nodes.keys()
    node_hostnames.sort()

    nodes_tuple_list = []
    for i in node_hostnames:
        nodes_tuple_list.append(nodes[i])

    nodes = nodes_tuple_list

    return render_to_response("ganeti/importing/nodes/import.html", {
        'nodes': nodes,
        'form':form,
        },
        context_instance=RequestContext(request),
    )
