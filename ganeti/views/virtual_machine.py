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

from time import sleep

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotFound, HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions import get_users, get_groups
from object_permissions.registration import perms_on_any
from object_permissions.views.permissions import view_users, view_permissions

from util.client import GanetiApiError
from ganeti.models import *
from util.portforwarder import forward_port
from util.client import GanetiApiError

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
        return HttpResponseForbidden()

    # Fancy HTTP methods. Yay?
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(["DELETE"])

    # Kill it with fire!
    jobid = instance.rapi.DeleteInstance(instance.hostname)
    sleep(2)
    jobstatus = instance.rapi.GetJobStatus(jobid)

    instance.delete()

    return HttpResponse('1', mimetype='application/json')

@login_required
def vnc(request, cluster_slug, instance):
    instance = get_object_or_404(VirtualMachine, hostname=instance)
    
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', instance) or \
        user.has_perm('admin', instance.cluster)):
        return HttpResponseForbidden('You do not have permission to vnc on this')
    
    #port, password = instance.setup_vnc_forwarding()
    
    host = instance.info['pnode']
    port = instance.info['network_port']
    password = ''
    
    return render_to_response("virtual_machine/vnc.html",
                              {'instance': instance,
                               'host': host,
                               'port': port,
                               'password': password},
        context_instance=RequestContext(request),
    )


@login_required
def shutdown(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user
    
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', vm.cluster)):
        return HttpResponseForbidden('You do not have permission to shut down this virtual machine')
    
    if request.method == 'POST':
        try:
            vm.shutdown()
            msg = [1, 'Virtual machine stopping.']
        except GanetiApiError, e:
            msg = [0, str(e)]
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', \
                                  'TRACE'])


@login_required
def startup(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', vm.cluster)):
            return HttpResponseForbidden('You do not have permission to start up this virtual machine')
    
    if request.method == 'POST':
        try:
            vm.startup()
            msg = [1, 'Virtual machine starting.']
        except GanetiApiError, e:
            msg = [0, str(e)]
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', \
                                  'TRACE'])


@login_required
def reboot(request, cluster_slug, instance):
    vm = get_object_or_404(VirtualMachine, hostname=instance, \
                           cluster__slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', vm.cluster)):
            return HttpResponseForbidden('You do not have permission to reboot this virtual machine')
    
    if request.method == 'POST':
        try:
            vm.reboot()
            msg = [1, 'Virtual machine rebooting.']
        except GanetiApiError, e:
            msg = [0, str(e)]
        return HttpResponse(json.dumps(msg), mimetype='application/json')
    return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', \
                                  'TRACE'])


@login_required
def list_(request):
    user = request.user
    if user.is_superuser:
        vms = VirtualMachine.objects.all()
        can_create = True
    else:
        vms = user.filter_on_perms(VirtualMachine, ['admin'])
        can_create = user.perms_on_any(Cluster, ['create_vm'])
    
    return render_to_response('virtual_machine/list.html', {
        'vms':vms,
        'can_create':can_create,
        },
        context_instance=RequestContext(request),
    )


@login_required
def detail(request, cluster_slug, instance):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance, cluster=cluster)
    
    user = request.user
    admin = user.is_superuser or user.has_perm('admin', vm) \
        or user.has_perm('admin', cluster)
    if not admin:
        return HttpResponseForbidden('You do not have permission to view this cluster\'s details')
    #TODO Update to use part of the NewVirtualMachineForm in 0.5 release
    """
    if request.method == 'POST':
        form = InstanceConfigForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
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
            form = InstanceConfigForm(vm.info['hvparams'])
        else:
            form = None
    """
    return render_to_response("virtual_machine/detail.html", {
        'cluster': cluster,
        'instance': vm,
        #'configform': form,
        'admin':admin
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
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    url = reverse('vm-permissions', args=[cluster.slug, vm.hostname])
    return view_users(request, vm, url)


@login_required
def permissions(request, cluster_slug, instance, user_id=None, group_id=None):
    """
    Update a users permissions.
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vm = get_object_or_404(VirtualMachine, hostname=instance)
    
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', vm) or \
        user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")

    url = reverse('vm-permissions', args=[cluster.slug, vm.hostname])
    return view_permissions(request, vm, url, user_id, group_id)


@login_required
def create(request, cluster_slug=None):
    """
    Create a new instance
        Store in DB and
        Create on given cluster
    """
    user = request.user
    if not(user.is_superuser or user.perms_on_any(Cluster, ['admin', 'create_vm'])):
        return HttpResponseForbidden('You do not have permission to create virtual \
                   machines')
    
    if cluster_slug is not None:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
    else:
        cluster = None

    if request.method == 'POST':
        form = NewVirtualMachineForm(user, None, request.POST)
        if form.is_valid():
            data = form.cleaned_data
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
            nictype = data['nictype']
            # HVPARAMS
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
                jobid = cluster.rapi.CreateInstance('create', hostname,
                        disk_template,
                        [{"size": disk_size, }],[{nicmode: nictype, }],
                        memory=ram, os=os, vcpus=vcpus,
                        pnode=pnode, snode=snode,
                        name_check=name_check, ip_check=name_check,
                        iallocator=iallocator_hostname,
                        hvparams={'kernel_path': kernelpath, \
                            'root_path': rootpath, \
                            'serial_console':serialconsole, \
                            'boot_order':bootorder, \
                            'cdrom_image_path':imagepath})
                
                # Wait for job to process as the error will not happen
                #  right away
                sleep(2)
                jobstatus = cluster.rapi.GetJobStatus(jobid)
                
                # raise an exception if there was an error in the job
                if jobstatus["status"] == 'error':
                    raise GanetiApiError(jobstatus["opresult"])
                    
                vm = VirtualMachine(cluster=cluster, owner=owner,
                                    hostname=hostname, disk_size=disk_size,
                                    ram=ram, virtual_cpus=vcpus)
                vm.save()
                
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
def cluster_choices(request):
    """
    Ajax view for looking up list of choices a user or usergroup has.  Returns
    the list of clusters a user has access to, or the list of clusters one of
    its groups has.
    """
    group_id = request.GET.get('group_id', None)
    
    GET = request.GET
    user = request.user
    if user.is_superuser:
        q = Cluster.objects.all()
    elif 'group_id' in GET:
        group = get_object_or_404(Group, id=GET['group_id'])
        if not group.user_set.filter(id=request.user.id).exists():
            return HttpResponseForbidden('not a member of this group')
        q = group.filter_on_perms(Cluster, ['admin','create_vm'])
    else:
        q = user.filter_on_perms(Cluster, ['admin','create_vm'], groups=False)
    
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
        return HttpResponseForbidden('You do not have permissions to view \
        this cluster')
    
    oslist = cluster_os_list(cluster)
    content = json.dumps({'nodes':cluster.nodes(), \
                          'os':oslist})
    return HttpResponse(content, mimetype='application/json')


def cluster_os_list(cluster):
    """
    A list of avaiable operating systems
    on the given cluster.
    """
    oses = cluster.rapi.GetOperatingSystems()
    # Given 'image+os-name'
    #  return formatted as 'Os Name'
    return [(os, " ".join([x.capitalize() for x in \
                os.replace('image+', '').split('-')])) \
                for os in oses]


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
        return HttpResponseForbidden('You do not have permission to view the default cluster options')
    
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
        'nictype':hvparams['nic_type'],
        'nicmode':info['nicparams']['default']['mode'],
        'kernelpath':hvparams['kernel_path'],
        'rootpath':hvparams['root_path'],
        'serialconsole':hvparams['serial_console'],
        'bootorder':hvparams['boot_order'],
        'imagepath':hvparams['cdrom_image_path'],
        }


class NewVirtualMachineForm(forms.Form):
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
    bootchoices = [
        ('disk', 'Hard Disk'),
        ('cdrom', 'CD-ROM')
    ]
    
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), label='Owner')
    cluster = forms.ModelChoiceField(queryset=Cluster.objects.all(), label='Cluster')
    hostname = forms.RegexField(label='Instance Name', regex=FQDN_RE,
                            error_messages={
                                'invalid': 'Instance name must be resolvable',
                            },
                            max_length=255)
    name_check = forms.BooleanField(label='DNS Name Check', \
                                    initial=True, required=False)
    iallocator = forms.BooleanField(label='Automatic Allocation', \
                                    initial=False, required=False)
    iallocator_hostname = forms.CharField(required=False)
    disk_template = forms.ChoiceField(label='Disk Template', \
                                      choices=templates)
    pnode = forms.ChoiceField(label='Primary Node', choices=[empty_field])
    snode = forms.ChoiceField(label='Secondary Node', choices=[empty_field])
    os = forms.ChoiceField(label='Operating System', choices=[empty_field])
    # BEPARAMS
    vcpus = forms.IntegerField(label='Virtual CPUs', min_value=1)
    ram = forms.IntegerField(label='Memory (MB)', min_value=100)
    disk_size = forms.IntegerField(label='Disk Size (MB)', min_value=100)
    nicmode = forms.ChoiceField(label='NIC Mode', choices=nicmodes)
    nictype = forms.ChoiceField(label='NIC Type', choices=nictypes)
    # HVPARAMS
    kernelpath = forms.CharField(label='Kernel Path', required=False)
    rootpath = forms.CharField(label='Root Path', initial='/')
    serialconsole = forms.BooleanField(label='Enable Serial Console',
                                      required=False)
    bootorder = forms.ChoiceField(label='Boot Device', choices=bootchoices)
    imagepath = forms.CharField(label='CD-ROM Image Path', required=False)
    
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
            self.fields['rootpath'].initial = defaults['rootpath']
            self.fields['kernelpath'].initial = defaults['kernelpath']
            self.fields['serialconsole'].initial = defaults['serialconsole']
        
        # set cluster choices based on the given owner
        if initial and 'owner' in initial and initial['owner']:
            try:
                self.owner = ClusterUser.objects.get(pk=initial['owner']).cast()
            except ClusterUser.DoesNotExist:
                self.owner = None
        else:
            self.owner = None
        
        # set choices based on user permissions and group membership
        if user.is_superuser:
            self.fields['owner'].queryset = ClusterUser.objects.all()
            self.fields['cluster'].queryset = Cluster.objects.all()
        else:
            choices = [(u'', u'---------')]
            choices += list(user.groups.values_list('id','name'))
            if user.perms_on_any(Cluster, ['admin','create_vm'], False):
                profile = user.get_profile()
                choices.append((profile.id, profile.name))
            self.fields['owner'].choices = choices
            
            # set cluster choices based on the given owner
            if self.owner:
                q = self.owner.filter_on_perms(Cluster, ['admin','create_vm'])
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
                quota = cluster.get_quota(owner)
                if quota.values():
                    used = owner.used_resources
                    if used['ram']:
                        ram = used['ram'] + data.get('ram', 0)
                        if ram > quota['ram']:
                            del data['ram']
                            q_msg = u"Owner does not have enough ram remaining on this cluster."
                            self._errors["ram"] = self.error_class([q_msg])
                    
                    if used['disk']:
                        disk = used['disk'] + data.get('disk_size', 0)
                        if disk > quota['disk']:
                           del data['disk_size']
                           q_msg = u"Owner does not have enough diskspace remaining on this cluster."
                           self._errors["disk_size"] = self.error_class([q_msg])
                    
                    if used['virtual_cpus']:
                        vcpus = used['virtual_cpus'] + data.get('vcpus', 0)
                        if vcpus > quota['virtual_cpus']:
                           del data['vcpus']
                           q_msg = u"Owner does not have enough virtual cpus remaining on this cluster."
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
                    response = urllib2.urlopen(data)
                    socket.setdefaulttimeout(oldtimeout)
                except ValueError:
                    socket.setdefaulttimeout(oldtimeout)
                    raise forms.ValidationError('%s is not a valid URL' % data)
                except: # urllib2 HTTP errors
                    socket.setdefaulttimeout(oldtimeout)
                    raise forms.ValidationError('Invalid URL')
        return data
