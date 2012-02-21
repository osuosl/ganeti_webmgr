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
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from ganeti_web.forms.importing import ImportForm, OrphanForm, VirtualMachineForm
from ganeti_web.middleware import Http403
from ganeti_web.models import VirtualMachine, Cluster
from ganeti_web.views.general import update_vm_counts
from django.utils.translation import ugettext as _


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
            raise Http403(_('You do not have sufficient privileges'))

    vms_with_cluster = VirtualMachine.objects.filter(owner=None, cluster__in=clusters) \
                          .order_by('hostname').values_list('id','hostname','cluster')

    if request.method == 'POST':
        # strip cluster from vms
        vms = [(i[0], i[1]) for i in vms_with_cluster]

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
            orphaned = defaultdict(lambda:0)
            for id in vm_ids:
                vm = VirtualMachine.objects.get(id=id)
                vm.owner = owner
                vm.save()
                orphaned[vm.cluster_id] -= 1
            update_vm_counts(key='orphaned', data=orphaned)

            # remove updated vms from the list
            vms_with_cluster = [i for i in vms_with_cluster
                if unicode(i[0]) not in vm_ids]

    else:
        # strip cluster from vms
        form = ImportForm([(i[0], i[1]) for i in vms_with_cluster])

    clusterdict = {}
    for i in clusters:
        clusterdict[i.id] = i.hostname
    vms = [ (i[0], clusterdict[i[2]], i[1]) for i in vms_with_cluster ]

    return render_to_response("ganeti/importing/orphans.html", {
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
            raise Http403(_('You do not have sufficient privileges'))

    vms = []
    for cluster in clusters:
        for vm in cluster.missing_in_ganeti:
            vms.append((vm, vm))

    if request.method == 'POST':
        # process updates if this was a form submission
        form = VirtualMachineForm(vms, request.POST)
        if form.is_valid():
            # update all selected VirtualMachines
            data = form.cleaned_data
            vm_ids = data['virtual_machines']
            q = VirtualMachine.objects.filter(hostname__in=vm_ids)

            missing = defaultdict(lambda:0)
            for i in q:
                missing[ i.cluster_id ] -= 1
            update_vm_counts(key='missing', data=missing)

            q.delete()

            # remove updated vms from the list
            vms = filter(lambda x: unicode(x[0]) not in vm_ids, vms)

    else:
        form = VirtualMachineForm(vms)

    vms = {}
    for cluster in clusters:
        for vm in cluster.missing_in_ganeti:
            vms[vm] = (cluster.hostname, vm)

    vmhostnames = vms.keys()
    vmhostnames.sort()

    vms_tuplelist = []
    for i in vmhostnames:
        vms_tuplelist.append((i, vms[i][0], vms[i][1]))

    vms = vms_tuplelist

    return render_to_response("ganeti/importing/missing.html", {
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
            raise Http403(_('You do not have sufficient privileges'))

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

            import_ready = defaultdict(lambda:0)
            orphaned = defaultdict(lambda:0)

            # create missing VMs
            for vm in vm_ids:
                cluster_id, host = vm.split(':')
                cluster = Cluster.objects.get(id=cluster_id)
                VirtualMachine(hostname=host, cluster=cluster, owner=owner).save()
                import_ready[cluster.pk] -= 1
                if owner is None:
                    orphaned[cluster.pk] += 1

            update_vm_counts(key='import_ready', data=import_ready)
            update_vm_counts(key='orphaned', data=orphaned)

            # remove created vms from the list
            vms = filter(lambda x: unicode(x[0]) not in vm_ids, vms)

    else:
        form = ImportForm(vms)

    vms = {}
    for cluster in clusters:
        for hostname in cluster.missing_in_db:
            vms[hostname] = ('%s:%s' % (cluster.id, hostname), cluster.hostname, hostname)
    vmhostnames = vms.keys()
    vmhostnames.sort()

    vms_tuplelist = []
    for i in vmhostnames:
        vms_tuplelist.append(vms[i])

    vms = vms_tuplelist

    return render_to_response("ganeti/importing/missing_db.html", {
        'vms': vms,
        'form':form,
        },
        context_instance=RequestContext(request),
    )
