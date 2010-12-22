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


from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from ganeti.models import VirtualMachine, Cluster, ClusterUser
from ganeti.views import render_403


class VirtualMachineForm(forms.Form):
    virtual_machines = forms.MultipleChoiceField()
    
    def __init__(self, choices, *args, **kwargs):
        super(VirtualMachineForm, self).__init__(*args, **kwargs)
        self.fields['virtual_machines'].choices = choices


class OrphanForm(VirtualMachineForm):
    """
    Form used for assigning owners to VirtualMachines that do not yet have an
    owner (orphans).
    """
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all())


class ImportForm(VirtualMachineForm):
    """
    Form used for assigning owners to VirtualMachines that do not yet have an
    owner (orphans).
    """
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), required=False)


@login_required
def orphans(request):
    """
    displays list of orphaned VirtualMachines, i.e. VirtualMachines without
    an owner.
    """
    user = request.user
    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_any_perms(Cluster, ['admin'])
        if not clusters:
            return render_403(request, 'You do not have sufficient privileges')
    
    vms = VirtualMachine.objects.filter(owner=None, cluster__in=clusters) \
                                            .values_list('id','hostname')
    vms = list(vms)
    vmcount = VirtualMachine.objects.count()
    
    if request.method == 'POST':
        # process updates if this was a form submission
        form = OrphanForm(vms, request.POST)
        if form.is_valid():
            # update all selected VirtualMachines
            data = form.cleaned_data
            owner = data['owner']
            vm_ids = data['virtual_machines']
            
            # update the owner and save the vm.  This isn't the most efficient
            # way of updating the VMs but we would otherwise need to group them
            # by cluster
            for id in vm_ids:
                vm = VirtualMachine.objects.get(id=id)
                vm.owner = owner
                vm.save()
            
            # remove updated vms from the list
            vms = filter(lambda x: unicode(x[0]) not in vm_ids, vms)
    
    else:
        form = ImportForm(vms)
    
    return render_to_response("importing/orphans.html", {
        'vms': vms,
        'form':form,
        },
        context_instance=RequestContext(request),
    )


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
            return render_403(request, 'You do not have sufficient privileges')
    
    vms = []
    for cluster in clusters:
        vms.extend(cluster.missing_in_ganeti)
    vms = zip(vms, vms)
    
    if request.method == 'POST':
        # process updates if this was a form submission
        form = VirtualMachineForm(vms, request.POST)
        if form.is_valid():
            # update all selected VirtualMachines
            data = form.cleaned_data
            vm_ids = data['virtual_machines']
            VirtualMachine.objects.filter(hostname__in=vm_ids).delete()
            
            # remove updated vms from the list
            vms = filter(lambda x: unicode(x[0]) not in vm_ids, vms)
    
    else:
        form = VirtualMachineForm(vms)
    
    return render_to_response("importing/missing.html", {
        'vms': vms,
        'form':form,
        },
        context_instance=RequestContext(request),
    )


@login_required
def missing_db(request):
    """
    View for displaying VirtualMachines missing from the database
    """
    user = request.user
    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_any_perms(Cluster, ['admin'])
        if not clusters:
            return render_403(request, 'You do not have sufficient privileges')
    
    vms = []
    for cluster in clusters:
        for hostname in cluster.missing_in_db:
            vms.append(('%s:%s' % (cluster.id, hostname), hostname))
    
    if request.method == 'POST':
        # process updates if this was a form submission
        form = ImportForm(vms, request.POST)
        if form.is_valid():
            # update all selected VirtualMachines
            data = form.cleaned_data
            owner = data['owner']
            vm_ids = data['virtual_machines']
            
            # create missing VMs
            for vm in vm_ids:
                cluster_id, host = vm.split(':')
                cluster = Cluster.objects.get(id=cluster_id)
                VirtualMachine(hostname=host, cluster=cluster, owner=owner).save()
            
            # remove created vms from the list
            vms = filter(lambda x: unicode(x[0]) not in vm_ids, vms)

    else:
        form = ImportForm(vms)
    
    return render_to_response("importing/missing_db.html", {
        'vms': vms,
        'form':form,
        },
        context_instance=RequestContext(request),
    )