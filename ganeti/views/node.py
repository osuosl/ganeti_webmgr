# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
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

import json

from django.contrib.auth.decorators import login_required
from django import forms
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from ganeti.utilities import cluster_default_info

from logs.models import LogItem
from logs.views import list_for_object
from util.client import GanetiApiError

log_action = LogItem.objects.log_action

from ganeti.models import Node, Cluster
from ganeti.views import render_403
from ganeti.views.virtual_machine import render_vms


@login_required
def detail(request, cluster_slug, host):
    """
    Renders a detail view for a Node
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)
    
    user = request.user
    admin = True if user.is_superuser else user.has_perm('admin', cluster)
    modify = True if admin else user.has_perm('migrate', cluster)
    if not (admin or modify):
        return render_403(request, "You do not have sufficient privileges")
    
    return render_to_response("node/detail.html", {
        'cluster':cluster,
        'node_count':cluster.nodes.all().count(),
        'node':node, 
        'admin':admin,
        'modify':modify,
        },
        context_instance=RequestContext(request),
    )


@login_required
def primary(request, cluster_slug, host):
    """
    Renders a list of primary VirtualMachines on the given node
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)
    
    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")

    vms = node.primary_vms.all()
    vms = render_vms(request, vms)

    return render_to_response("virtual_machine/table.html",
                {'tableID': 'table_primary', 'node': node, 'vms':vms},
                context_instance=RequestContext(request))


@login_required
def secondary(request, cluster_slug, host):
    """
    Renders a list of secondary VirtualMachines on the given node
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)
    
    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")

    vms = node.secondary_vms.all()
    vms = render_vms(request, vms)

    return render_to_response("virtual_machine/table.html",
                {'tableID': 'table_secondary', 'node': node, 'vms':vms},
                context_instance=RequestContext(request))

@login_required
def object_log(request, cluster_slug, host):
    """
    Display object log for this node
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")

    return list_for_object(request, node)


class RoleForm(forms.Form):
    """
    Form for editing roles
    """
    ROLE_CHOICES = (
        ('', '-------------'),
        ('master-candidate','Master Candidate'),
        ('regular','Regular'),
        ('drained','Drained'),
        ('offline','Offline'),
    )
    
    # map of role codes to form fields
    ROLE_MAP = {
        'C':'master-candidate',
        'R':'regular',
        'D':'drained',
        'O':'offline',
    }
    
    role = forms.ChoiceField(initial='', choices=ROLE_CHOICES, label='New Role')
    force = forms.BooleanField(initial=False, required=False)

@login_required
def role(request, cluster_slug, host):
    """
    view used for setting node role
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)
    
    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            try:
                job = node.set_role(form.cleaned_data['role'])
                job.load_info()
                msg = job.info

                # log information
                log_action('NODE_ROLE_CHANGE', user, node)
                return HttpResponse(json.dumps(msg), mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__':[str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')
        
    elif node.role == 'M':
        # XXX master isn't a possible choice for changing role
        form = RoleForm()
        
    else:
        data = {'role':RoleForm.ROLE_MAP[node.role]}
        form = RoleForm(data)
    
    return render_to_response('node/role.html', \
        {'form':form, 'node':node, 'cluster':cluster}, \
        context_instance=RequestContext(request))


class MigrateForm(forms.Form):
    """ Form used for migrating primary Virtual Machines off a Node """
    MODE_CHOICES = (
        ('live','Live'),
        ('non-live','Non-Live'),
    )

    mode = forms.ChoiceField(choices=MODE_CHOICES)



@login_required
def migrate(request, cluster_slug, host):
    """
    view used for initiating a Node Migrate job
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)
    
    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")
    
    if request.method == 'POST':
        form = MigrateForm(request.POST)
        if form.is_valid():
            try:
                job = node.migrate(form.cleaned_data['mode'])
                job.load_info()
                msg = job.info

                # log information
                log_action('NODE_MIGRATE', user, node)

                return HttpResponse(json.dumps(msg), mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__':[str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')
        
    else:
        form = MigrateForm()
    
    return render_to_response('node/migrate.html', \
        {'form':form, 'node':node, 'cluster':cluster}, \
        context_instance=RequestContext(request))


class EvacuateForm(forms.Form):
    EMPTY_FIELD = (u'', u'---------')

    iallocator = forms.BooleanField(initial=False, required=False, \
                                    label='Automatic Allocation')
    iallocator_hostname = forms.CharField(initial='', required=False, \
                                    widget = forms.HiddenInput())
    node = forms.ChoiceField(initial='', choices=[EMPTY_FIELD], required=False)

    def __init__(self, cluster, node, *args, **kwargs):
        super(EvacuateForm, self).__init__(*args, **kwargs)

        node_list = [str(h) for h in cluster.nodes.exclude(pk=node.pk)\
                                    .values_list('hostname', flat=True)]
        nodes = zip(node_list, node_list)
        nodes.insert(0, self.EMPTY_FIELD)
        self.fields['node'].choices = nodes

        defaults = cluster_default_info(cluster)
        if defaults['iallocator'] != '' :
            self.fields['iallocator'].initial = True
            self.fields['iallocator_hostname'].initial = defaults['iallocator']

    def clean(self):
        data = self.cleaned_data
        
        iallocator = data['iallocator']
        node = data['node'] if 'node' in data else None

        if iallocator:
            data['node'] = None
        elif node:
            data['iallocator_hostname'] = None
        else:
            raise ValidationError('Must choose automatic allocation or a specific node')

        return data


@login_required
def evacuate(request, cluster_slug, host):
    """
    view used for initiating a node evacuate job
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    node = get_object_or_404(Node, hostname=host)
    
    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")

    if request.method == 'POST':
        form = EvacuateForm(cluster, node, request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                evacuate_node = data['node']
                iallocator_hostname = data['iallocator_hostname']
                job = node.evacuate(iallocator_hostname, evacuate_node)
                job.load_info()
                msg = job.info

                # log information
                log_action('NODE_EVACUATE', user, node, job)

                return HttpResponse(json.dumps(msg), mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__':[str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    else:
        form = EvacuateForm(cluster, node)

    return render_to_response('node/evacuate.html', \
        {'form':form, 'node':node, 'cluster':cluster}, \
        context_instance=RequestContext(request))

