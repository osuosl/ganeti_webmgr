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
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.forms import CharField, HiddenInput
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings

from logs.views import list_for_object

from object_permissions.views.permissions import view_users, view_permissions
from object_permissions import get_users_any
from object_permissions import signals as op_signals

from logs.models import LogItem
log_action = LogItem.objects.log_action

from util.client import GanetiApiError
from ganeti.models import Cluster, ClusterUser, Organization, VirtualMachine, \
        Job, SSHKey
from ganeti.views import render_403
from ganeti.forms.virtual_machine import NewVirtualMachineForm, \
    ModifyVirtualMachineForm, ModifyConfirmForm, MigrateForm
from ganeti.templatetags.webmgr_tags import render_storage
from ganeti.utilities import cluster_default_info, cluster_os_list, \
    compare


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

        # log information
        log_action('VM_REINSTALL', user, instance)

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
            log_action('VM_STOP', user, vm)
        except GanetiApiError, e:
            msg = {'__all__':[str(e)]}
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
            log_action('VM_START', user, vm)
        except GanetiApiError, e:
            msg = {'__all__':[str(e)]}
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['POST'])


@login_required
def migrate(request, cluster_slug, instance):
    """
    view used for initiating a Node Migrate job
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster, ['admin','migrate'])):
        return render_403(request, "You do not have sufficient privileges")

    if request.method == 'POST':
        form = MigrateForm(request.POST)
        if form.is_valid():
            try:
                job = vm.migrate(form.cleaned_data['mode'])
                job.load_info()
                msg = job.info

                # log information
                log_action('VM_MIGRATE', user, vm)

                return HttpResponse(json.dumps(msg), mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__':[str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    else:
        form = MigrateForm()

    return render_to_response('virtual_machine/migrate.html', \
        {'form':form, 'vm':vm, 'cluster':cluster}, \
        context_instance=RequestContext(request))


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
            log_action('VM_RESTART', user, vm)
        except GanetiApiError, e:
            msg = {'__all__':[str(e)]}
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
        migrate = True
        tags = True
    else:
        remove = user.has_perm('remove', vm)
        power = user.has_perm('power', vm)
        modify = user.has_perm('modify', vm)
        tags = user.has_perm('tags', vm)
        migrate = user.has_perm('migrate', cluster)
    
    if not (admin or power or remove or modify or tags):
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
        'migrate':migrate,
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
def object_log(request, cluster_slug, instance):
    """
    Display all of the Users of a VirtualMachine
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', cluster)):
        return render_403(request, "You do not have sufficient privileges")

    return list_for_object(request, vm)


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
                log_action('CREATE', user, vm)

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
    if not (user.is_superuser or user.has_perm('admin', vm) \
        or user.has_perm('modify', vm)):
        return render_403(request, 'You do not have permissions to edit \
            this virtual machine')

    if request.method == 'POST':
        form = ModifyVirtualMachineForm(user, None, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.session['edit_form'] = data

            return HttpResponseRedirect( \
            reverse('instance-modify-confirm', args=[cluster.slug, vm.hostname]))

    elif request.method == 'GET':              
        if 'edit_form' in request.session:
            form = ModifyVirtualMachineForm(user, cluster, request.session['edit_form'])
            del request.session['edit_form']
        else:
            # Need to set initial values from vm.info as these are not saved
            #  per the vm model.
            if vm.info and 'hvparams' in vm.info:
                info = vm.info
                initial = {}
                hvparams = info['hvparams']
                # XXX Convert ram string since it comes out
                #  from ganeti as an int and the DataVolumeField does not like
                #  ints.
                initial['vcpus'] = info['beparams']['vcpus']
                initial['ram'] = str(info['beparams']['memory'])
                initial['disk_type'] = hvparams['disk_type']
                initial['bootorder'] = hvparams['boot_order']
                initial['nictype'] = hvparams['nic_type']
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
def modify_confirm(request, cluster_slug, instance):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance, cluster=cluster)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) \
        or user.has_perm('modify', vm)):
        return render_403(request, 'You do not have permissions to edit \
            this virtual machine')

    if request.method == "POST":
        form = ModifyConfirmForm(request.POST)
        if form.is_valid():
            data = form.data
            if 'edit' in request.POST:
                return HttpResponseRedirect( \
                    reverse("instance-modify", \
                    args=[cluster.slug, vm.hostname]))
            elif 'reboot' in request.POST or 'save' in request.POST:
                # Modify Instance rapi call
                rapi_dict = json.loads(data['rapi_dict'])
                job_id = cluster.rapi.ModifyInstance(instance,
                    nics=[(0, {'link':rapi_dict['niclink'], }),], \
                    hvparams={'kernel_path': rapi_dict['kernelpath'], \
                        'root_path': rapi_dict['rootpath'], \
                        'serial_console':rapi_dict['serialconsole'], \
                        'boot_order':rapi_dict['bootorder'], \
                        'nic_type':rapi_dict['nictype'], \
                        'disk_type':rapi_dict['disk_type'], \
                        'cdrom_image_path':rapi_dict['imagepath']}, \
                    beparams={'vcpus':rapi_dict['vcpus'],'memory': rapi_dict['ram']}
                )
                # Create job and update message on virtual machine detail page
                job = Job.objects.create(job_id=job_id, obj=vm, cluster=cluster)
                VirtualMachine.objects.filter(id=vm.id).update(last_job=job, \
                                                           ignore_cache=True)
                # log information about modifying this instance
                log_action('EDIT', user, vm)
                if 'reboot' in request.POST and vm.info['status'] == 'running':
                    if not (user.is_superuser or user.has_perm('power', vm)):
                        return render_403(request, "Sorry, but you do not have permission to reboot \
                        this machine.")
                    else:
                        # Reboot the vm
                        vm.reboot()
                        log_action('VM_REBOOT', user, vm)

            # Remove session variables.
            if 'edit_form' in request.session:
                del request.session['edit_form']
            # Redirect to instance-detail
            return HttpResponseRedirect( \
                reverse("instance-detail", args=[cluster.slug, vm.hostname]))

    if request.method == "GET":
        form = ModifyConfirmForm()
        session = request.session

        if not 'edit_form' in request.session:  
            return HttpResponseBadRequest('Incorrect Session Data')

        data = session['edit_form']
        info = vm.info
        hvparams = info['hvparams']

        old_set = dict(
            bootorder=hvparams['boot_order'],
            disk_type=hvparams['disk_type'],
            imagepath=hvparams['cdrom_image_path'],
            kernelpath=hvparams['kernel_path'],
            niclink=info['nic.links'][0],
            nictype=hvparams['nic_type'],
            ram=info['beparams']['memory'],
            rootpath=hvparams['root_path'],
            serialconsole=hvparams['serial_console'],
            vcpus=info['beparams']['vcpus'],
        )
        
        new_set = dict(
            bootorder=data['bootorder'],
            disk_type=data['disk_type'],
            imagepath=data['imagepath'],
            kernelpath=data['kernelpath'],
            niclink=data['niclink'],
            nictype=data['nictype'],
            ram=data['ram'],
            rootpath=data['rootpath'],
            serialconsole=data['serialconsole'],
            vcpus=data['vcpus'],
        )

        instance_diff = {}
        for key in old_set.keys():
            if key == 'ram':
                diff = compare(render_storage(old_set[key]), \
                    render_storage(new_set[key]))
            else:
                diff = compare(old_set[key], new_set[key])
            if diff != "":
                instance_diff[key] = diff

        form.fields['rapi_dict'] = CharField(widget=HiddenInput, \
            initial=json.dumps(new_set)) 

    return render_to_response('virtual_machine/edit_confirm.html', {
        'cluster': cluster,
        'form': form,
        'instance': vm,
        'instance_diff': instance_diff,
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
    nodes = [str(h) for h in cluster.nodes.values_list('hostname', flat=True)]
    content = json.dumps({'nodes':nodes, 'os':oslist})
    return HttpResponse(content, mimetype='application/json')


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


def recv_user_add(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_add_user, Logs action
    """
    log_action('ADD_USER', editor, obj, user)


def recv_user_remove(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_remove_user, Logs action
    """
    log_action('REMOVE_USER', editor, obj, user)


def recv_perm_edit(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_edit_user, Logs action
    """
    log_action('MODIFY_PERMS', editor, obj, user)


op_signals.view_add_user.connect(recv_user_add, sender=VirtualMachine)
op_signals.view_remove_user.connect(recv_user_remove, sender=VirtualMachine)
op_signals.view_edit_user.connect(recv_perm_edit, sender=VirtualMachine)
