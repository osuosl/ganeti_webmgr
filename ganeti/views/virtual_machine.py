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

from collections import defaultdict
import json
import socket
import urllib2

# XXX Sleep is used current in 3 places because ganeti takes a few seconds to process jobs.
#  Information on whether or not an operation succeeded is gathered from ganeti in this aspect
#  thus the extra 2 second wait. This should go away once logging has been fully implemented so
#  a user of the system can no if their job succeeded or failed.
from time import sleep

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings

from object_permissions.views.permissions import view_users, view_permissions
from object_permissions import get_users_any
from object_permissions import signals as op_signals

from logs.models import LogItem
log_action = LogItem.objects.log_action

from util.client import GanetiApiError
from ganeti.models import Cluster, ClusterUser, Organization, VirtualMachine, \
        Job, SSHKey, VirtualMachineTemplate
from ganeti.views import render_403
from ganeti.fields import DataVolumeField

empty_field = (u'', u'---------')


@login_required
def delete(request, cluster_slug, instance):
    """
    Delete a VM.
    """

    user = request.user
    instance = get_object_or_404(VirtualMachine, cluster__slug=cluster_slug,
        hostname=instance)

    # Check permissions.
    if not (
        user.is_superuser or
        user.has_perm("remove", instance) or
        user.has_perm("admin", instance) or
        user.has_perm("admin", instance.cluster)
        ):
        return render_403(request, 'You do not have sufficient privileges')
    
    if request.method == 'GET':
        return render_to_response("virtual_machine/delete.html",
            {'vm': instance},
            context_instance=RequestContext(request),
        )
    
    elif request.method == 'POST':
        # start deletion job and mark the VirtualMachine as pending_delete and
        # disable the cache for this VM.
        job_id = instance.rapi.DeleteInstance(instance.hostname)
        job = Job.objects.create(job_id=job_id, obj=instance, cluster_id=instance.cluster_id)
        VirtualMachine.objects.filter(id=instance.id) \
            .update(last_job=job, ignore_cache=True, pending_delete=True)
        
        return HttpResponseRedirect( \
            reverse('instance-detail', args=[cluster_slug, instance.hostname]))

    return HttpResponseNotAllowed(["GET","POST"])


@login_required
def reinstall(request, cluster_slug, instance):
    """
    Reinstall a VM.
    """

    user = request.user
    instance = get_object_or_404(VirtualMachine, cluster__slug=cluster_slug,
        hostname=instance)

    # Check permissions.
    # XXX Reinstalling is somewhat similar to deleting in that you destroy data,
    # so use that for now.
    if not (
        user.is_superuser or
        user.has_any_perms(instance, ["remove", "admin"]) or
        user.has_perm("admin", instance.cluster)
        ):
        return render_403(request, 'You do not have sufficient privileges')

    if request.method == 'GET':
        return render_to_response("virtual_machine/reinstall.html",
            {'vm': instance, 'oschoices': cluster_os_list(instance.cluster),
             'current_os': instance.operating_system, 'submitted': False},
            context_instance=RequestContext(request),
        )
      
    elif request.method == 'POST':
        # Reinstall instance
        if "os" in request.POST:
            os = request.POST["os"]
        else:
            os = instance.operating_system

        # XXX no_startup=True prevents quota circumventions. possible future solution would be a checkbox
        # asking whether they want to start up, and check quota here if they do (would also involve
        # checking whether this VM is already running and subtracting that)
        
        job_id = instance.rapi.ReinstallInstance(instance.hostname, os=os, no_startup=True)
        job = Job.objects.create(job_id=job_id, obj=instance, cluster=instance.cluster)
        VirtualMachine.objects.filter(id=instance.id).update(last_job=job, ignore_cache=True)
        
        return HttpResponseRedirect(
            reverse('instance-detail', args=[instance.cluster.slug, instance.hostname]))
    
    return HttpResponseNotAllowed(["GET","POST"])


@login_required
def novnc(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser \
        or user.has_any_perms(vm, ['admin', 'power']) \
        or user.has_perm('admin', vm.cluster)):
            return HttpResponseForbidden('You do not have permission to vnc on this')

    return render_to_response("virtual_machine/novnc.html",
                              {'cluster_slug': cluster_slug,
                               'instance': vm,
                               },
        context_instance=RequestContext(request),
    )


@login_required
def vnc_proxy(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                                 cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser \
        or user.has_any_perms(vm, ['admin', 'power']) \
        or user.has_perm('admin', vm.cluster)):
            return HttpResponseForbidden('You do not have permission to vnc on this')
    
    result = json.dumps(vm.setup_vnc_forwarding())
    
    return HttpResponse(result, mimetype="application/json")


@login_required
def shutdown(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user

    if not (user.is_superuser or user.has_any_perms(vm, ['admin','power']) or \
        user.has_perm('admin', vm.cluster)):
        return render_403(request, 'You do not have permission to shut down this virtual machine')

    if request.method == 'POST':
        try:
            job = vm.shutdown()
            job.load_info()
            msg = job.info
            
            # log information about stopping the machine
            log_action(user, vm, "stopped")
        except GanetiApiError, e:
            msg = [0, str(e)]
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['POST'])


@login_required
def startup(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_any_perms(vm, ['admin','power']) or \
        user.has_perm('admin', vm.cluster)):
            return render_403(request, 'You do not have permission to start up this virtual machine')

    # superusers bypass quota checks
    if not user.is_superuser and vm.owner:
        # check quota
        quota = vm.cluster.get_quota(vm.owner)
        if any(quota.values()):
            used = vm.owner.used_resources(vm.cluster, only_running=True)
            
            if quota['ram'] is not None and (used['ram'] + vm.ram) > quota['ram']:
                msg = 'Owner does not have enough RAM remaining on this cluster to start the virtual machine.'
                return HttpResponse(json.dumps([0, msg]), mimetype='application/json')
            
            if quota['virtual_cpus'] and (used['virtual_cpus'] + vm.virtual_cpus) > quota['virtual_cpus']:
                msg = 'Owner does not have enough Virtual CPUs remaining on this cluster to start the virtual machine.'
                return HttpResponse(json.dumps([0, msg]), mimetype='application/json')

    if request.method == 'POST':
        try:
            job = vm.startup()
            job.load_info()
            msg = job.info
            
            # log information about starting up the machine
            log_action(user, vm, "started")
        except GanetiApiError, e:
            msg = [0, str(e)]
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['POST'])


@login_required
def reboot(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_any_perms(vm, ['admin','power']) or \
        user.has_perm('admin', vm.cluster)):
            return render_403(request, 'You do not have permission to reboot this virtual machine')

    if request.method == 'POST':
        try:
            job = vm.reboot()
            job.load_info()
            msg = job.info
            
            # log information about restarting the machine
            log_action(user, vm, "restarted")
        except GanetiApiError, e:
            msg = [0, str(e)]
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['POST'])


def ssh_keys(request, cluster_slug, instance, api_key):
    """
    Show all ssh keys which belong to users, who are specified vm's admin
    """
    if settings.WEB_MGR_API_KEY != api_key:
        return HttpResponseForbidden("You're not allowed to view keys.")

    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)

    users = get_users_any(vm, ["admin",]).values_list("id",flat=True)
    keys = SSHKey.objects.filter(user__in=users).values_list('key','user__username').order_by('user__username')

    keys_list = list(keys)
    return HttpResponse(json.dumps(keys_list), mimetype="application/json")


def render_vms(request, query):
    """
    Helper function for paginating a virtual machine query
    """
    GET = request.GET
    if 'order_by' in GET:
        query = query.order_by(GET['order_by'])
    count = GET['count'] if 'count' in GET else settings.ITEMS_PER_PAGE
    paginator = Paginator(query, count)
    page = request.GET.get('page', 1)

    try:
        vms = paginator.page(page)
    except (EmptyPage, InvalidPage):
        vms = paginator.page(paginator.num_pages)

    return vms


@login_required
def list_(request):
    """
    View for displaying a list of VirtualMachines
    """
    user = request.user

    # there are 3 cases
    #1) user is superuser
    if user.is_superuser:
        vms = VirtualMachine.objects.all()
        can_create = True

    #2) user has any perms on any VM
    #3) user belongs to the group which has perms on any VM
    else:
        vms = user.get_objects_any_perms(VirtualMachine, groups=True, \
                                        cluster=['admin'])
        can_create = user.has_any_perms(Cluster, ['create_vm', ])

    vms = vms.select_related()

    # paginate, sort
    vms = render_vms(request, vms)

    return render_to_response('virtual_machine/list.html', {
        'vms':vms,
        'can_create':can_create,
        },
        context_instance=RequestContext(request),
    )


@login_required
def vm_table(request, cluster_slug=None):
    """
    View for displaying the virtual machine table.  This is used for ajax calls
    to reload the table.   Usually because of a page or sort change.
    """
    user = request.user

    # there are 3 cases
    #1) user is superuser
    if user.is_superuser:
        vms = VirtualMachine.objects.all()
        can_create = True

    #2) user has any perms on any VM
    #3) user belongs to the group which has perms on any VM
    else:
        vms = user.get_objects_any_perms(VirtualMachine, groups=True, cluster=['admin'])
        can_create = user.has_any_perms(Cluster, ['create_vm'])

    if cluster_slug:
        cluster = Cluster.objects.get(slug=cluster_slug)
        vms = vms.filter(cluster=cluster)
    else:
        cluster = None

    vms = render_vms(request, vms)

    return render_to_response('virtual_machine/inner_table.html', {
        'vms':vms,
        'can_create':can_create,
        'cluster':cluster
       },
        context_instance=RequestContext(request),
    )


@login_required
def detail(request, cluster_slug, instance):
    """
    Display details of virtual machine.
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance, cluster=cluster)

    user = request.user
    cluster_admin = user.is_superuser or user.has_perm('admin', cluster)
    admin = cluster_admin or user.has_perm('admin', vm) \
    
    if admin:
        remove = True
        power = True
        modify = True
    else:
        remove = user.has_perm('remove', vm)
        power = user.has_perm('power', vm)
        modify = user.has_perm('modify', vm)
    
    if not (admin or power or remove):
        return render_403(request, 'You do not have permission to view this cluster\'s details')
	
    if vm.pending_delete:
        template = 'virtual_machine/delete_status.html' 
    else:
        template = 'virtual_machine/detail.html'
    
    return render_to_response(template, {
        'cluster': cluster,
        'instance': vm,
        'admin':admin,
        'cluster_admin':cluster_admin,
        'remove':remove,
        'power':power,
        'modify':modify,
        },
        context_instance=RequestContext(request),
    )


@login_required
def users(request, cluster_slug, instance):
    """
    Display all of the Users of a VirtualMachine
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', cluster)):
        return render_403(request, "You do not have sufficient privileges")

    url = reverse('vm-permissions', args=[cluster.slug, vm.hostname])
    return view_users(request, vm, url)


@login_required
def permissions(request, cluster_slug, instance, user_id=None, group_id=None):
    """
    Update a users permissions.
    """
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', vm.cluster)):
        return render_403(request, "You do not have sufficient privileges")

    url = reverse('vm-permissions', args=[cluster_slug, vm.hostname])
    return view_permissions(request, vm, url, user_id, group_id)


@login_required
def create(request, cluster_slug=None):
    """
    Create a new instance
        Store in DB and
        Create on given cluster
    """
    user = request.user
    if not(user.is_superuser or user.has_any_perms(Cluster, ['admin', 'create_vm'])):
        return render_403(request, 'You do not have permission to create virtual \
                   machines')

    if cluster_slug is not None:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
    else:
        cluster = None

    if request.method == 'POST':
        form = NewVirtualMachineForm(user, None, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            start = data['start']
            owner = data['owner']
            cluster = data['cluster']
            hostname = data['hostname']
            disk_template = data['disk_template']
            # Default to not pass in pnode and snode
            #  since these will be set if the form is correct
            pnode = None
            snode = None
            os = data['os']
            name_check = data['name_check']
            iallocator = data['iallocator']
            # Hidden fields
            iallocator_hostname = None
            if 'iallocator_hostname' in data:
                iallocator_hostname = data['iallocator_hostname']
            # BEPARAMS
            vcpus = data['vcpus']
            disk_size = data['disk_size']
            ram = data['ram']
            nicmode = data['nicmode']
            niclink = data['niclink']
            nictype = data['nictype']
            # HVPARAMS
            disktype = data['disk_type']

            kernelpath = data['kernelpath']
            rootpath = data['rootpath']
            serialconsole = data['serialconsole']
            bootorder = data['bootorder']
            imagepath = data['imagepath']

            # If iallocator was not checked do not pass in the iallocator
            #  name. If iallocator was checked don't pass snode,pnode.
            if not iallocator:
                iallocator_hostname = None
                pnode = data['pnode']

            # If drbd is being used assign the secondary node
            if disk_template == 'drbd' and pnode is not None:
                snode = data['snode']

            try:
                # XXX attempt to load the virtual machine.  This ensure that if
                # there was a previous vm with the same hostname, but had not
                # successfully been deleted, then it will be deleted now
                try:
                    VirtualMachine.objects.get(cluster=cluster, hostname=hostname)
                except VirtualMachine.DoesNotExist:
                    pass
                
                job_id = cluster.rapi.CreateInstance('create', hostname,
                        disk_template,
                        [{"size": disk_size, }],[{'mode':nicmode, 'link':niclink, }],
                        start=start, os=os, vcpus=vcpus,
                        pnode=pnode, snode=snode,
                        name_check=name_check, ip_check=name_check,
                        iallocator=iallocator_hostname,
                        hvparams={'kernel_path': kernelpath, \
                            'root_path': rootpath, \
                            'serial_console':serialconsole, \
                            'boot_order':bootorder, \
                            'nic_type':nictype, \
                            'disk_type':disktype,\
                            'cdrom_image_path':imagepath},
                        beparams={"memory": ram})
                
                vm = VirtualMachine(cluster=cluster, owner=owner,
                                    hostname=hostname, disk_size=disk_size,
                                    ram=ram, virtual_cpus=vcpus)
                vm.ignore_cache = True
                vm.save()
                job = Job.objects.create(job_id=job_id, obj=vm, cluster=cluster)
                VirtualMachine.objects.filter(id=vm.id).update(last_job=job)

                # log information about creating the machine
                log_action(user, vm, "created")

                # grant admin permissions to the owner
                data['grantee'].grant('admin', vm)

                return HttpResponseRedirect( \
                reverse('instance-detail', args=[cluster.slug, vm.hostname]))

            except GanetiApiError, e:
                msg = 'Error creating virtual machine on this cluster: %s' % e
                form._errors["cluster"] = form.error_class([msg])

    elif request.method == 'GET':
        form = NewVirtualMachineForm(user, cluster)

    return render_to_response('virtual_machine/create.html', {
        'form': form
        },
        context_instance=RequestContext(request),
    )


@login_required
def modify(request, cluster_slug, instance):     
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance, cluster=cluster)

    user = request.user
    admin = user.is_superuser or user.has_perm('admin', vm) \
        or user.has_perm('admin', cluster)

    if request.method == 'POST':
        form = ModifyVirtualMachineForm(user, None, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            vcpus = data['vcpus']
            ram = data['ram']
            disksize = data['disk_size']
            disktype = data['disk_type']
            bootorder = data['bootorder']
            nictype = data['nictype']
            nicmode = data['nicmode']
            niclink = data['niclink']
            rootpath = data['rootpath']
            kernelpath = data['kernelpath']
            serialconsole = data['serialconsole']
            imagepath = data['imagepath']
            """
            cluster.rapi.ModifyInstance(instance, \
                        hvparams={'kernel_path': kernelpath, \
                            'root_path': rootpath, \
                            'serial_console':serialconsole, \
                            'boot_order':bootorder, \
                            'nic_type':nictype, \
                            'disk_type':disktype,\
                            'cdrom_image_path':imagepath},
                        beparams={"memory": ram})
            """
            """
            return HttpResponseRedirect( \
            reverse('instance-detail', args=[cluster.slug, vm.hostname]))
            """
            """
            if data['cdrom_type'] == 'none':
                data['cdrom_image_path'] = 'none'
            elif data['cdrom_image_path'] != vm.hvparams['cdrom_image_path']:
                # This should be an http URL
                if not (data['cdrom_image_path'].startswith('http://') or
                        data['cdrom_image_path'] == 'none'):
                    # Remove this, we don't want them to be able to read local files
                    del data['cdrom_image_path']
            vm.set_params(**data)
            sleep(1)
            return HttpResponseRedirect(request.path)
            
            else:
                if vm.info:
                    if vm.info['hvparams']['cdrom_image_path']:
                        vm.info['hvparams']['cdrom_type'] = 'iso'
                    else:
                        vm.info['hvparams']['cdrom_type'] = 'none'
                    form = EditVirtualMachineForm(vm.info['hvparams'])
                else:
                    form = None
            """

    elif request.method == 'GET':              
        # Need to set initial values from vm.info as these are not saved
        #  per the vm model.
        # initial = vm.info
        if vm.info and 'hvparams' in vm.info:
            info = vm.info
            initial = {}
            hvparams = info['hvparams']
            # XXX Convert ram, and disk_size to str since they come out
            #  from ganeti as ints, and the DataVolumeField does not like
            #  ints.
            initial['vcpus'] = info['beparams']['vcpus']
            initial['ram'] = str(info['beparams']['memory'])
            initial['disk_size'] = str(info['disk.sizes'][0])
            initial['disk_type'] = hvparams['disk_type']
            initial['bootorder'] = hvparams['boot_order']
            initial['nictype'] = hvparams['nic_type']
            initial['nicmode'] = info['nic.modes'][0]
            initial['niclink'] = info['nic.links'][0]
            initial['rootpath'] = hvparams['root_path']
            initial['kernelpath'] = hvparams['kernel_path']
            initial['serialconsole'] = hvparams['serial_console']
            initial['imagepath'] = hvparams['cdrom_image_path']
        form = ModifyVirtualMachineForm(user, cluster, initial=initial)

    return render_to_response("virtual_machine/edit.html", {
        'cluster': cluster,
        'instance': vm,
        'form': form,
        },
        context_instance=RequestContext(request),
    )


@login_required
def cluster_choices(request):
    """
    Ajax view for looking up list of choices a user or usergroup has.  Returns
    the list of clusters a user has access to, or the list of clusters one of
    its groups has.
    """
    clusteruser_id = request.GET.get('clusteruser_id', None)

    user = request.user
    if user.is_superuser:
        q = Cluster.objects.all()
    elif clusteruser_id is not None:
        clusteruser = get_object_or_404(ClusterUser, id=clusteruser_id).cast()
        if isinstance(clusteruser, Organization):
            target = clusteruser.group
        else:
            target = clusteruser.user
        q = target.get_objects_any_perms(Cluster, ["admin", "create_vm"])
    else:
        q = user.get_objects_any_perms(Cluster, ['admin','create_vm'], False)

    clusters = list(q.values_list('id', 'hostname'))
    content = json.dumps(clusters)
    return HttpResponse(content, mimetype='application/json')


@login_required
def cluster_options(request):
    """
    Ajax view for retrieving node and operating system choices for a given
    cluster.
    """
    cluster_id = request.GET.get('cluster_id', None)
    cluster = get_object_or_404(Cluster, id__exact=cluster_id)

    user = request.user
    if not (user.is_superuser or user.has_perm('create_vm', cluster) or \
            user.has_perm('admin', cluster)):
        return render_403(request, 'You do not have permissions to view \
        this cluster')

    oslist = cluster_os_list(cluster)
    content = json.dumps({'nodes':cluster.nodes(), \
                          'os':oslist})
    return HttpResponse(content, mimetype='application/json')


def cluster_os_list(cluster):
    """
    Create a detailed manifest of available operating systems on the cluster.
    """

    return os_prettify(cluster.rapi.GetOperatingSystems())

def os_prettify(oses):
    """
    Pretty-print and format a list of operating systems.

    The actual format is a list of tuples of tuples. The first entry in the
    outer tuple is a label, and then each successive entry is a tuple of the
    actual Ganeti OS name, and a prettified display name. For example:

    [
        ("Image",
            ("image+obonto-hungry-hydralisk", "Obonto Hungry Hydralisk"),
            ("image+fodoro-core", "Fodoro Core"),
        ),
        ("Dobootstrop",
            ("dobootstrop+dobion-lotso", "Dobion Lotso"),
        ),
    ]
    """

    # In order to convince Django to make optgroups, we need to nest our
    # iterables two-deep. (("header", ("value, "label"), ("value", "label")))
    # http://docs.djangoproject.com/en/dev/ref/models/fields/#choices
    # We do this by making a dict of lists.
    d = defaultdict(list)

    for name in oses:
        try:
            # Split into type and flavor.
            t, flavor = name.split("+", 1)
            # Prettify flavors. "this-boring-string" becomes "This Boring String"
            flavor = " ".join(word.capitalize() for word in flavor.split("-"))
            d[t.capitalize()].append((name, flavor))
        except ValueError:
            d["Unknown"].append((name, name))

    l = d.items()
    l.sort()

    return l

@login_required
def cluster_defaults(request):
    """
    Ajax view for retrieving the default cluster options to be set
    on the NewVirtualMachineForm.
    """
    cluster_id = request.GET.get('cluster_id', None)
    cluster = get_object_or_404(Cluster, id__exact=cluster_id)

    user = request.user
    if not (user.is_superuser or user.has_perm('create_vm', cluster) or \
            user.has_perm('admin', cluster)):
        return render_403(request, 'You do not have permission to view the default cluster options')

    content = json.dumps(cluster_default_info(cluster))
    return HttpResponse(content, mimetype='application/json')


def cluster_default_info(cluster):
    """
    Returns a dictionary containing the following
    default values set on a cluster:
        iallocator, hypervisors, vcpus, ram, nictype,
        nicmode, kernelpath, rootpath, serialconsole,
        bootorder, imagepath
    """
    # Create variables so that dictionary lookups are not so horrendous.
    info = cluster.info
    beparams = info['beparams']['default']
    hv = info['default_hypervisor']
    hvparams = info['hvparams'][hv]

    try:
        iallocator_info = info['default_iallocator']
    except:
        iallocator_info = None

    return {
        'iallocator': iallocator_info,
        'hypervisors':info['enabled_hypervisors'],
        'vcpus':beparams['vcpus'],
        'ram':beparams['memory'],
        'disktype':hvparams['disk_type'],
        'nictype':hvparams['nic_type'],
        'nicmode':info['nicparams']['default']['mode'],
        'niclink':info['nicparams']['default']['link'],
        'kernelpath':hvparams['kernel_path'],
        'rootpath':hvparams['root_path'],
        'serialconsole':hvparams['serial_console'],
        'bootorder':hvparams['boot_order'],
        'imagepath':hvparams['cdrom_image_path'],
        }


class NewVirtualMachineForm(forms.ModelForm):
    """
    Virtual Machine Creation / Edit form
    """
    FQDN_RE = r'(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)'

    templates = [
        (u'', u'---------'),
        (u'plain', u'plain'),
        (u'drbd', u'drbd'),
        (u'file', u'file'),
        (u'diskless', u'diskless')
    ]
    nicmodes = [
        (u'', u'---------'),
        (u'routed', u'routed'),
        (u'bridged', u'bridged')
    ]
    nictypes = [
        (u'', u'---------'),
        (u'rtl8139',u'rtl8139'),
        (u'ne2k_isa',u'ne2k_isa'),
        (u'ne2k_pci',u'ne2k_pci'),
        (u'i82551',u'i82551'),
        (u'i82557b',u'i82557b'),
        (u'i82559er',u'i82559er'),
        (u'pcnet',u'pcnet'),
        (u'e1000',u'e1000'),
        (u'paravirtual',u'paravirtual'),
    ]
    disktypes = [
        (u'', u'---------'),
        (u'paravirtual',u'paravirtual'),
        (u'ioemu',u'ioemu'),
        (u'ide',u'ide'),
        (u'scsi',u'scsi'),
        (u'sd',u'sd'),
        (u'mtd',u'mtd'),
        (u'pflash',u'pflash'),
    ]
    bootchoices = [
        ('disk', 'Hard Disk'),
        ('cdrom', 'CD-ROM'),
        ('network', 'Network'),
    ]

    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), label='Owner')
    cluster = forms.ModelChoiceField(queryset=Cluster.objects.none(), label='Cluster')
    hostname = forms.RegexField(label='Instance Name', regex=FQDN_RE,
                            error_messages={
                                'invalid': 'Instance name must be resolvable',
                            },
                            max_length=255)
    pnode = forms.ChoiceField(label='Primary Node', choices=[empty_field])
    snode = forms.ChoiceField(label='Secondary Node', choices=[empty_field])
    os = forms.ChoiceField(label='Operating System', choices=[empty_field])
    disk_template = forms.ChoiceField(label='Disk Template', \
                                      choices=templates)
    ram = DataVolumeField(label='Memory', min_value=100)
    disk_size = DataVolumeField(label='Disk Size', min_value=100)
    disk_type = forms.ChoiceField(label='Disk Type', choices=disktypes)
    nicmode = forms.ChoiceField(label='NIC Mode', choices=nicmodes)
    nictype = forms.ChoiceField(label='NIC Type', choices=nictypes)
    bootorder = forms.ChoiceField(label='Boot Device', choices=bootchoices)

    class Meta:
        model = VirtualMachineTemplate

    def __init__(self, user, cluster=None, initial=None, *args, **kwargs):
        self.user = user
        super(NewVirtualMachineForm, self).__init__(initial, *args, **kwargs)

        if initial:
            if 'cluster' in initial and initial['cluster']:
                try:
                    cluster = Cluster.objects.get(pk=initial['cluster'])
                except Cluster.DoesNotExist:
                    # defer to clean function to return errors
                    pass
        if cluster is not None:
            # set choices based on selected cluster if given
            oslist = cluster_os_list(cluster)
            nodelist = cluster.nodes()
            nodes = zip(nodelist, nodelist)
            nodes.insert(0, empty_field)
            oslist.insert(0, empty_field)
            self.fields['pnode'].choices = nodes
            self.fields['snode'].choices = nodes
            self.fields['os'].choices = oslist

            defaults = cluster_default_info(cluster)
            if defaults['iallocator'] != '' :
                self.fields['iallocator'].initial = True
                self.fields['iallocator_hostname'] = forms.CharField( \
                                        initial=defaults['iallocator'], \
                                        required=False, \
                                        widget = forms.HiddenInput())
            self.fields['vcpus'].initial = defaults['vcpus']
            self.fields['ram'].initial = defaults['ram']
            self.fields['disk_type'].initial = defaults['disktype']
            self.fields['rootpath'].initial = defaults['rootpath']
            self.fields['kernelpath'].initial = defaults['kernelpath']
            self.fields['serialconsole'].initial = defaults['serialconsole']
            self.fields['niclink'].initial = defaults['niclink']

        # set cluster choices based on the given owner
        if initial and 'owner' in initial and initial['owner']:
            try:
                self.owner = ClusterUser.objects.get(pk=initial['owner']).cast()
            except ClusterUser.DoesNotExist:
                self.owner = None
        else:
            self.owner = None

        # Set up owner and cluster choices.
        if user.is_superuser:
            # Superusers may do whatever they like.
            self.fields['owner'].queryset = ClusterUser.objects.all()
            self.fields['cluster'].queryset = Cluster.objects.all()
        else:
            # Fill out owner choices. Remember, the list of owners is a list
            # of tuple(ClusterUser.id, label). If you put ids from other
            # Models into this, no magical correction will be applied and you
            # will assign permissions to the wrong owner; see #2007.
            owners = [(u'', u'---------')]
            for group in user.groups.all():
                owners.append((group.organization.id, group.name))
            if user.has_any_perms(Cluster, ['admin','create_vm'], False):
                profile = user.get_profile()
                owners.append((profile.id, profile.name))
            self.fields['owner'].choices = owners

            # Set cluster choices.  If an owner has been selected then filter
            # by the owner.  Otherwise show everything the user has access to
            # through themselves or any groups they are a member of
            if self.owner:
                q = self.owner.get_objects_any_perms(Cluster, ['admin','create_vm'])
            else:
                q = user.get_objects_any_perms(Cluster, ['admin','create_vm'])
            self.fields['cluster'].queryset = q

    def clean(self):
        data = self.cleaned_data

        owner = self.owner
        if owner:
            if isinstance(owner, (Organization,)):
                grantee = owner.group
            else:
                grantee = owner.user
            data['grantee'] = grantee

        # superusers bypass all permission and quota checks
        if not self.user.is_superuser and owner:
            msg = None

            if isinstance(owner, (Organization,)):
                # check user membership in group if group
                if not grantee.user_set.filter(id=self.user.id).exists():
                    msg = u"User is not a member of the specified group."

            else:
                if not owner.user_id == self.user.id:
                    msg = "You are not allowed to act on behalf of this user."

            # check permissions on cluster
            if 'cluster' in data:
                cluster = data['cluster']
                if not (owner.has_perm('create_vm', cluster) \
                        or owner.has_perm('admin', cluster)):
                    msg = u"Owner does not have permissions for this cluster."

                # check quota
                start = data['start']
                quota = cluster.get_quota(owner)
                if quota.values():
                    used = owner.used_resources(cluster, only_running=True)
                    
                    if start and quota['ram'] is not None and \
                        (used['ram'] + data['ram']) > quota['ram']:
                            del data['ram']
                            q_msg = u"Owner does not have enough ram remaining on this cluster. You may choose to not automatically start the instance or reduce the amount of ram."
                            self._errors["ram"] = self.error_class([q_msg])
                    
                    if quota['disk'] and used['disk'] + data['disk_size'] > quota['disk']:
                        del data['disk_size']
                        q_msg = u"Owner does not have enough diskspace remaining on this cluster."
                        self._errors["disk_size"] = self.error_class([q_msg])
                    
                    if start and quota['virtual_cpus'] is not None and \
                        (used['virtual_cpus'] + data['vcpus']) > quota['virtual_cpus']:
                            del data['vcpus']
                            q_msg = u"Owner does not have enough virtual cpus remaining on this cluster. You may choose to not automatically start the instance or reduce the amount of virtual cpus."
                            self._errors["vcpus"] = self.error_class([q_msg])
            
            if msg:
                self._errors["owner"] = self.error_class([msg])
                del data['owner']

        pnode = data.get("pnode", '')
        snode = data.get("snode", '')
        iallocator = data.get('iallocator', False)
        iallocator_hostname = data.get('iallocator_hostname', '')
        disk_template = data.get("disk_template")

        # Need to have pnode != snode
        if disk_template == "drbd" and not iallocator:
            if pnode == snode and (pnode != '' or snode != ''):
                # We know these are not in self._errors now
                msg = u"Primary and Secondary Nodes must not match."
                self._errors["pnode"] = self.error_class([msg])

                # These fields are no longer valid. Remove them from the
                # cleaned data.
                del data["pnode"]
                del data["snode"]
        else:
            if "snode" in self._errors:
                del self._errors["snode"]

        # If boot_order = CD-ROM make sure imagepath is set as well.
        boot_order = data.get('bootorder', '')
        image_path = data.get('imagepath', '')
        if boot_order == 'cdrom':
            if image_path == '':
                msg = u'Image path required if boot device is CD-ROM.'
                self._errors["imagepath"] = self.error_class([msg])

                del data["imagepath"]
                del data["bootorder"]

        if iallocator:
            # If iallocator is checked,
            #  don't display error messages for nodes
            if iallocator_hostname != '':
                if 'pnode' in self._errors:
                    del self._errors['pnode']
                if 'snode' in self._errors:
                    del self._errors['snode']
            else:
                msg = u'Automatic Allocation was selected, but there is no \
                      IAllocator available.'
                self._errors['iallocator'] = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return data


class ModifyVirtualMachineForm(NewVirtualMachineForm):

    exclude = ('start', 'owner', 'cluster', 'hostname', 'name_check',
        'iallocator', 'iallocator_hostname', 'disk_template', 'pnode', 'snode',\
        'os')

    class Meta:
        model = VirtualMachineTemplate

    def __init__(self, user, cluster, initial=None, *args, **kwargs):
        super(ModifyVirtualMachineForm, self).__init__(user, cluster=cluster, \
                initial=initial, *args, **kwargs)
        # Remove all fields in the form that are not required to modify the 
        #   instance.
        for field in self.exclude:
            del self.fields[field]

class InstanceConfigForm(forms.Form):
    nic_type = forms.ChoiceField(label="Network adapter model",
                                 choices=(('paravirtual', 'Paravirtualized'),
                                          ('rtl8139', 'Realtek 8139+'),
                                          ('e1000', 'Intel PRO/1000'),
                                          ('ne2k_pci', 'NE2000 PCI')))

    disk_type = forms.ChoiceField(label="Hard disk type",
                                  choices=(('paravirtual', 'Paravirtualized'),
                                           ('scsi', 'SCSI'),
                                           ('ide', 'IDE')))

    boot_order = forms.ChoiceField(label="Boot device",
                                   choices=(('disk', 'Hard disk'),
                                            ('cdrom', 'CDROM')))

    cdrom_type = forms.ChoiceField(label="CD-ROM Drive",
                                   choices=(('none', 'Disabled'),
                                            ('iso', 'ISO Image over HTTP (see below)')),
                                   widget=forms.widgets.RadioSelect())

    cdrom_image_path = forms.CharField(required=False, label="ISO Image URL (http)")
    use_localtime = forms.BooleanField(label="Hardware clock uses local time instead of UTC", required=False)

    def clean_cdrom_image_path(self):
        data = self.cleaned_data['cdrom_image_path']
        if data:
            if not (data == 'none' or data.startswith('http://')):
                raise forms.ValidationError('Only HTTP URLs are allowed')

            elif data != 'none':
                # Check if the image is there
                oldtimeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(5)
                try:
                    print "Trying to open"
                    urllib2.urlopen(data)
                except ValueError:
                    raise forms.ValidationError('%s is not a valid URL' % data)
                except: # urllib2 HTTP errors
                    raise forms.ValidationError('Invalid URL')
                finally:
                    socket.setdefaulttimeout(oldtimeout)
        return data


def recv_user_add(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_add_user, Logs action
    """
    log_action(editor, obj, "added user")


def recv_user_remove(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_remove_user, Logs action
    """
    log_action(editor, obj, "removed user")


def recv_perm_edit(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_edit_user, Logs action
    """
    log_action(editor, obj, "modified permissions")


op_signals.view_add_user.connect(recv_user_add, sender=VirtualMachine)
op_signals.view_remove_user.connect(recv_user_remove, sender=VirtualMachine)
op_signals.view_edit_user.connect(recv_perm_edit, sender=VirtualMachine)
