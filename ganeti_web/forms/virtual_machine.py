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
import copy

from django import forms
from django.forms import ValidationError
# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from ganeti_web.constants import EMPTY_CHOICE_FIELD, HV_DISK_TEMPLATES, \
    HV_NIC_MODES, HV_DISK_TYPES, HV_NIC_TYPES, KVM_NIC_TYPES, HVM_DISK_TYPES, \
    KVM_DISK_TYPES, KVM_BOOT_ORDER, HVM_BOOT_ORDER, KVM_CHOICES, HV_USB_MICE, \
    HV_SECURITY_MODELS, KVM_FLAGS, HV_DISK_CACHES, MODE_CHOICES, HVM_CHOICES, \
    HV_DISK_TEMPLATES_SINGLE_NODE
from ganeti_web.fields import DataVolumeField, MACAddressField
from ganeti_web.models import (Cluster, ClusterUser, Organization,
                           VirtualMachineTemplate, VirtualMachine)
from ganeti_web.utilities import cluster_default_info, cluster_os_list, contains, get_hypervisor
from django.utils.translation import ugettext_lazy as _
from ganeti_web.util.client import REPLACE_DISK_AUTO, REPLACE_DISK_PRI, \
    REPLACE_DISK_CHG, REPLACE_DISK_SECONDARY


class VirtualMachineForm(forms.ModelForm):
    """
    Parent class that holds all vm clean methods
      and shared form fields.
    """
    memory = DataVolumeField(label=_('Memory'), min_value=100)

    class Meta:
        model = VirtualMachineTemplate

    def clean_hostname(self):
        data = self.cleaned_data
        hostname = data.get('hostname')
        cluster = data.get('cluster')
        if hostname and cluster:
            # Verify that this hostname is not in use for this cluster.  It can
            # only be reused when recovering a VM that failed to deploy.
            #
            # Recoveries are only allowed when the user is the owner of the VM
            try:
                vm = VirtualMachine.objects.get(cluster=cluster, hostname=hostname)

                # detect vm that failed to deploy
                if not vm.pending_delete and vm.template is not None:
                    current_owner = vm.owner.cast()
                    if current_owner == self.owner:
                        data['vm_recovery'] = vm
                    else:
                        msg = _("Owner cannot be changed when recovering a failed deployment")
                        self._errors["owner"] = self.error_class([msg])
                else:
                    raise ValidationError(_("Hostname is already in use for this cluster"))

            except VirtualMachine.DoesNotExist:
                # doesn't exist, no further checks needed
                pass

        return hostname

    def clean_vcpus(self):
        vcpus = self.cleaned_data.get("vcpus", None)

        if vcpus is not None and vcpus < 1:
            self._errors["vcpus"] = self.error_class(
                ["At least one CPU must be present"])
        else:
            return vcpus

    def clean_initrd_path(self):
        data = self.cleaned_data['initrd_path']
        if data and not data.startswith('/') and data != 'no_initrd_path':
            msg = u"%s." % _('This field must start with a "/"')
            self._errors['initrd_path'] = self.error_class([msg])
        return data

    def clean_security_domain(self):
        data = self.cleaned_data['security_domain']
        security_model = self.cleaned_data['security_model']
        msg = None

        if data and security_model != 'user':
            msg = u'%s.' % _(
                'This field can not be set if Security Mode is not set to User')
        elif security_model == 'user':
            if not data:
                msg = u'%s.' % _('This field is required')
            elif not data[0].isalpha():
                msg = u'%s.' % _('This field must being with an alpha character')

        if msg:
            self._errors['security_domain'] = self.error_class([msg])
        return data

    def clean_vnc_x509_path(self):
        data = self.cleaned_data['vnc_x509_path']
        if data and not data.startswith('/'):
            msg = u'%s,' % _('This field must start with a "/"')
            self._errors['vnc_x509_path'] = self.error_class([msg])
        return data


class NewVirtualMachineForm(VirtualMachineForm):
    """
    Virtual Machine Creation form
    """
    pvm_exclude_fields = ('disk_type','nic_type', 'boot_order', 'serial_console',
        'cdrom_image_path')

    empty_field = EMPTY_CHOICE_FIELD
    templates = HV_DISK_TEMPLATES
    templates_single = HV_DISK_TEMPLATES_SINGLE_NODE
    nicmodes = HV_NIC_MODES

    disk_count = forms.IntegerField(initial=1,  widget=forms.HiddenInput())
    nic_count = forms.IntegerField(initial=1, widget=forms.HiddenInput())
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), label=_('Owner'))
    cluster = forms.ModelChoiceField(queryset=Cluster.objects.none(), label=_('Cluster'))
    hypervisor = forms.ChoiceField(required=False, choices=[empty_field])
    hostname = forms.CharField(label=_('Instance Name'), max_length=255)
    pnode = forms.ChoiceField(label=_('Primary Node'), choices=[empty_field])
    snode = forms.ChoiceField(label=_('Secondary Node'), choices=[empty_field])
    os = forms.ChoiceField(label=_('Operating System'), choices=[empty_field])
    disk_template = forms.ChoiceField(label=_('Disk Template'),
                                      choices=templates)
    disk_type = forms.ChoiceField(label=_('Disk Type'), choices=[empty_field])
    nic_type = forms.ChoiceField(label=_('NIC Type'), choices=[empty_field])
    boot_order = forms.ChoiceField(label=_('Boot Device'), choices=[empty_field])

    class Meta(VirtualMachineForm.Meta):
        exclude = ('template_name')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        initial = kwargs.get('initial', None)

        # If data is not passed by initial kwarg (as in POST data)
        #   assign initial to self.data as self.data contains POST
        #   data.
        if initial is None and args:
            initial = args[0]

        cluster = None
        if initial:
            if 'cluster' in initial and initial['cluster']:
                try:
                    cluster = Cluster.objects.get(pk=initial['cluster'])
                except Cluster.DoesNotExist:
                    # defer to clean function to return errors
                    pass

            # Load disks and nics. Prefer raw fields, but unpack from dicts
            # if the raw fields are not available.  This allows modify and
            # API calls to use a cleaner syntax
            if 'disks' in initial and not 'disk_count' in initial:
                disks = initial['disks']
                initial['disk_count'] = disk_count = len(disks)
                for i, disk in enumerate(disks):
                    initial['disk_size_%s' % i] = disk['size']
            else:
                disk_count = int(initial.get('disk_count', 1))
            if 'nics' in initial and not 'nic_count' in initial:
                nics = initial['nics']
                initial['nic_count'] = nic_count = len(nics)
                for i, disk in enumerate(nics):
                    initial['nic_mode_%s' % i] = disk['mode']
                    initial['nic_link_%s' % i] = disk['link']
            else:
                nic_count = int(initial.get('nic_count', 1))
        else:
            disk_count = 1
            nic_count = 1

        super(NewVirtualMachineForm, self).__init__(*args, **kwargs)

        # Make sure vcpus is required for this form. Don't want to go through
        #  the trouble of overriding the model field.
        self.fields['vcpus'].required = True

        if cluster is not None and cluster.info is not None:
            # set choices based on selected cluster if given
            oslist = cluster_os_list(cluster)
            nodelist = [str(h) for h in cluster.nodes.values_list('hostname', flat=True)]
            nodes = zip(nodelist, nodelist)
            nodes.insert(0, self.empty_field)
            oslist.insert(0, self.empty_field)
            self.fields['pnode'].choices = nodes
            self.fields['snode'].choices = nodes
            self.fields['os'].choices = oslist

            # must have at least two nodes to use drbd
            if len(nodes) == 2:
                choices = self.fields['disk_template'].choices = self.templates_single

            hv = initial.get('hypervisor', None)
            if hv is not None:
                defaults = cluster_default_info(cluster, hv)
            else:
                defaults = cluster_default_info(cluster)
                hv = defaults['hypervisor']
            if defaults['iallocator'] != '' :
                self.fields['iallocator'].initial = True
                self.fields['iallocator_hostname'] = forms.CharField(
                                        initial=defaults['iallocator'],
                                        required=False,
                                        widget = forms.HiddenInput())
            self.fields['vcpus'].initial = defaults['vcpus']
            self.fields['memory'].initial = defaults['memory']
            self.fields['hypervisor'].choices = defaults['hypervisors']
            self.fields['hypervisor'].initial = hv
            self.create_nic_fields(nic_count, defaults)

            if hv == 'kvm':
                self.fields['serial_console'].initial = defaults['serial_console']


            # Set field choices and hypervisor
            if hv == 'kvm' or hv == 'xen-pvm':
                self.fields['root_path'].initial = defaults['root_path']
                self.fields['kernel_path'].initial = defaults['kernel_path']
            if hv == 'kvm' or hv == 'xen-hvm':
                self.fields['nic_type'].choices = defaults['nic_types']
                self.fields['disk_type'].choices = defaults['disk_types']
                self.fields['boot_order'].choices = defaults['boot_devices']

                self.fields['nic_type'].initial = defaults['nic_type']
                self.fields['disk_type'].initial = defaults['disk_type']
                self.fields['boot_order'].initial = defaults['boot_order']
            if hv == 'xen-pvm':
                for field in self.pvm_exclude_fields:
                    del self.fields[field]
        else:
            self.create_nic_fields(nic_count)

        self.create_disk_fields(disk_count)

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
    
    def create_disk_fields(self, count):
        """
        dynamically add fields for disks
        """
        self.disk_fields = range(count)
        for i in range(count):
            disk_size = DataVolumeField(min_value=100, required=True,
                                        label=_("Disk/%s Size" % i))
            self.fields['disk_size_%s'%i] = disk_size

    def create_nic_fields(self, count, defaults=None):
        """
        dynamically add fields for nics
        """
        self.nic_fields = range(count)
        for i in range(count):
            nic_mode = forms.ChoiceField(label=_('NIC/%s Mode' % i), choices=HV_NIC_MODES)
            nic_link = forms.CharField(label=_('NIC/%s Link' % i), max_length=255)
            if defaults is not None:
                nic_link.initial = defaults['nic_link']
            self.fields['nic_mode_%s'%i] = nic_mode
            self.fields['nic_link_%s'%i] = nic_link

    def clean_cluster(self):
        # Invalid or unavailable cluster
        cluster = self.cleaned_data.get('cluster', None)
        if cluster is None or cluster.info is None:
            msg = u"%s." % _("This cluster is currently unavailable. Please check for Errors on the \
                cluster detail page")
            self._errors['cluster'] = self.error_class([msg])
        return cluster
    
    def clean(self):
        data = self.cleaned_data

        # First things first. Let's do any error-checking and validation which
        # requires combinations of data but doesn't require hitting the DB.

        pnode = data.get("pnode", '')
        snode = data.get("snode", '')
        iallocator = data.get('iallocator', False)
        iallocator_hostname = data.get('iallocator_hostname', '')
        disk_template = data.get("disk_template")

        # Need to have pnode != snode
        if disk_template == "drbd" and not iallocator:
            if pnode == snode and (pnode != '' or snode != ''):
                # We know these are not in self._errors now
                msg = u"%s." % _("Primary and Secondary Nodes must not match")
                self._errors["pnode"] = self.error_class([msg])

                # These fields are no longer valid. Remove them from the
                # cleaned data.
                del data["pnode"]
                del data["snode"]
        else:
            if "snode" in self._errors:
                del self._errors["snode"]

        # If boot_order = CD-ROM make sure imagepath is set as well.
        boot_order = data.get('boot_order', '')
        image_path = data.get('cdrom_image_path', '')
        if boot_order == 'cdrom':
            if image_path == '':
                msg = u"%s." % _("Image path required if boot device is CD-ROM")
                self._errors["cdrom_image_path"] = self.error_class([msg])
                del data["cdrom_image_path"]

        if iallocator:
            # If iallocator is checked,
            #  don't display error messages for nodes
            if iallocator_hostname != '':
                if 'pnode' in self._errors:
                    del self._errors['pnode']
                if 'snode' in self._errors:
                    del self._errors['snode']
            else:
                msg = u"%s." % _(
                    "Automatic Allocation was selected, but there is no IAllocator available.")
                self._errors['iallocator'] = self.error_class([msg])

        # If there are any errors, exit early.
        if self._errors:
            return data

        # From this point, database stuff is alright.

        owner = self.owner
        if owner:
            if isinstance(owner, (Organization,)):
                grantee = owner.group
            else:
                grantee = owner.user
            data['grantee'] = grantee

        # sum disk sizes and build disks param for input into ganeti
        disk_sizes = [data.get('disk_size_%s' % i) for i in xrange(data.get('disk_count'))]
        disk_size = sum(disk_sizes)
        data['disk_size'] = disk_size
        data['disks'] = [dict(size=size) for size in disk_sizes]

        # build nics dictionaries
        nics = []
        for i in xrange(data.get('nic_count')):
            nics.append(dict(mode=data.get('nic_mode_%s' % i),
                             link=data.get('nic_link_%s' % i)))
        data['nics'] = nics

        # superusers bypass all permission and quota checks
        if not self.user.is_superuser and owner:
            msg = None

            if isinstance(owner, (Organization,)):
                # check user membership in group if group
                if not grantee.user_set.filter(id=self.user.id).exists():
                    msg = u"%s." % _("User is not a member of the specified group")

            else:
                if not owner.user_id == self.user.id:
                    msg = u"%s." % _("You are not allowed to act on behalf of this user")

            # check permissions on cluster
            if 'cluster' in data:
                cluster = data['cluster']
                if not (owner.has_perm('create_vm', cluster)
                        or owner.has_perm('admin', cluster)):
                    msg = u"%s." % _("Owner does not have permissions for this cluster")

                # check quota
                start = data['start']
                quota = cluster.get_quota(owner)
                if quota.values():
                    used = owner.used_resources(cluster, only_running=True)

                    if (start and quota['ram'] is not None and
                        (used['ram'] + data['memory']) > quota['ram']):
                            del data['memory']
                            q_msg = u"%s" % _("Owner does not have enough ram remaining on this cluster. You may choose to not automatically start the instance or reduce the amount of ram.")
                            self._errors["ram"] = self.error_class([q_msg])

                    if quota['disk'] and used['disk'] + data['disk_size'] > quota['disk']:
                        del data['disk_size']
                        q_msg = u"%s" % _("Owner does not have enough diskspace remaining on this cluster.")
                        self._errors["disk_size"] = self.error_class([q_msg])

                    if (start and quota['virtual_cpus'] is not None and
                        (used['virtual_cpus'] + data['vcpus']) >
                        quota['virtual_cpus']):
                            del data['vcpus']
                            q_msg = u"%s" % _("Owner does not have enough virtual cpus remaining on this cluster. You may choose to not automatically start the instance or reduce the amount of virtual cpus.")
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
                msg = u"%s." % _("Primary and Secondary Nodes must not match")
                self._errors["pnode"] = self.error_class([msg])

                # These fields are no longer valid. Remove them from the
                # cleaned data.
                del data["pnode"]
                del data["snode"]
        else:
            if "snode" in self._errors:
                del self._errors["snode"]

        # If boot_order = CD-ROM make sure imagepath is set as well.
        boot_order = data.get('boot_order', '')
        image_path = data.get('cdrom_image_path', '')
        if boot_order == 'cdrom':
            if image_path == '':
                msg = u"%s." % _("Image path required if boot device is CD-ROM")
                self._errors["cdrom_image_path"] = self.error_class([msg])
                del data["cdrom_image_path"]

        if iallocator:
            # If iallocator is checked,
            #  don't display error messages for nodes
            if iallocator_hostname != '':
                if 'pnode' in self._errors:
                    del self._errors['pnode']
                if 'snode' in self._errors:
                    del self._errors['snode']
            else:
                msg = u"%s." % _("Automatic Allocation was selected, but there is no \
                      IAllocator available.")
                self._errors['iallocator'] = self.error_class([msg])

        # Check options which depend on the the hypervisor type
        hv = data.get('hypervisor')
        disk_type = data.get('disk_type')
        nic_type = data.get('nic_type')

        # Check disk_type
        if (hv == 'kvm' and not (contains(disk_type, KVM_DISK_TYPES) or contains(disk_type, HV_DISK_TYPES))) or \
           (hv == 'xen-hvm' and not (contains(disk_type, HVM_DISK_TYPES) or contains(disk_type, HV_DISK_TYPES))):
            msg = '%s is not a valid option for Disk Template on this cluster.' % disk_type
            self._errors['disk_type'] = self.error_class([msg])
        # Check nic_type
        if (hv == 'kvm' and not (contains(nic_type, KVM_NIC_TYPES) or \
           contains(nic_type, HV_NIC_TYPES))) or \
           (hv == 'xen-hvm' and not contains(nic_type, HV_NIC_TYPES)):
            msg = '%s is not a valid option for Nic Type on this cluster.' % nic_type
            self._errors['nic_type'] = self.error_class([msg])
        # Check boot_order 
        if (hv == 'kvm' and not contains(boot_order, KVM_BOOT_ORDER)) or \
           (hv == 'xen-hvm' and not contains(boot_order, HVM_BOOT_ORDER)):
            msg = '%s is not a valid option for Boot Device on this cluster.' % boot_order
            self._errors['boot_order'] = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return data


def check_quota_modify(form):
    """ method for validating user is within their quota when modifying """
    data = form.cleaned_data
    cluster = form.cluster
    owner = form.owner
    vm = form.vm

    # check quota
    if owner is not None:
        start = data['start']
        quota = cluster.get_quota(owner)
        if quota.values():
            used = owner.used_resources(cluster, only_running=True)

            if (start and quota['ram'] is not None and
                (used['ram'] + data['memory']-vm.ram) > quota['ram']):
                    del data['memory']
                    q_msg = u"%s" % _("Owner does not have enough ram remaining on this cluster. You must reduce the amount of ram.")
                    form._errors["ram"] = form.error_class([q_msg])

            if 'disk_size' in data and data['disk_size']:
                if quota['disk'] and used['disk'] + data['disk_size'] > quota['disk']:
                    del data['disk_size']
                    q_msg = u"%s" % _("Owner does not have enough diskspace remaining on this cluster.")
                    form._errors["disk_size"] = form.error_class([q_msg])

            if (start and quota['virtual_cpus'] is not None and
                (used['virtual_cpus'] + data['vcpus'] - vm.virtual_cpus) >
                quota['virtual_cpus']):
                    del data['vcpus']
                    q_msg = u"%s" % _("Owner does not have enough virtual cpus remaining on this cluster. You must reduce the amount of virtual cpus.")
                    form._errors["vcpus"] = form.error_class([q_msg])


class ModifyVirtualMachineForm(VirtualMachineForm):
    """
    Base modify class.
        If hvparam_fields (itirable) set on child, then
        each field on the form will be initialized to the
        value in vm.info.hvparams
    """
    always_required = ('vcpus', 'memory')
    empty_field = EMPTY_CHOICE_FIELD

    nic_count = forms.IntegerField(initial=1, widget=forms.HiddenInput())
    os = forms.ChoiceField(label=_('Operating System'), choices=[empty_field])

    class Meta:
        model = VirtualMachineTemplate
        exclude = ('start', 'owner', 'cluster', 'hostname', 'name_check',
        'iallocator', 'iallocator_hostname', 'disk_template', 'pnode', 'nics',
        'snode','disk_size', 'nic_mode', 'template_name', 'hypervisor', 'disks')

    def __init__(self, vm, initial=None, *args, **kwargs):
        super(VirtualMachineForm, self).__init__(initial, *args, **kwargs)

        # Set owner on form
        try:
            self.owner
        except AttributeError:
            self.owner = vm.owner

        # Setup os choices
        os_list = cluster_os_list(vm.cluster)
        self.fields['os'].choices = os_list

        for field in self.always_required:
            self.fields[field].required = True
        # If the required property is set on a child class,
        #  require those form fields   
        try:
            if self.required:
                for field in self.required:
                    self.fields[field].required = True
        except AttributeError:
            pass

        # Need to set initial values from vm.info as these are not saved
        #  per the vm model.
        if vm.info:
            info = vm.info
            hvparam = info['hvparams']
            # XXX Convert ram string since it comes out
            #  from ganeti as an int and the DataVolumeField does not like
            #  ints.
            self.fields['vcpus'].initial = info['beparams']['vcpus']
            self.fields['memory'].initial = str(info['beparams']['memory'])

            # always take the larger nic count.  this ensures that if nics are
            # being removed that they will be in the form as Nones
            self.nics = len(info['nic.links'])
            nic_count = int(initial.get('nic_count', 1)) if initial else 1
            nic_count = self.nics if self.nics > nic_count else nic_count
            self.fields['nic_count'].initial = nic_count
            self.nic_fields = xrange(nic_count)
            for i in xrange(nic_count):
                link = forms.CharField(label=_('NIC/%s Link' % i), max_length=255, required=True)
                self.fields['nic_link_%s' % i] = link
                mac = MACAddressField(label=_('NIC/%s Mac' % i), required=True)
                self.fields['nic_mac_%s' % i] = mac
                if i < self.nics:
                    mac.initial = info['nic.macs'][i]
                    link.initial = info['nic.links'][i]

            self.fields['os'].initial = info['os']
            
            try:
                if self.hvparam_fields:
                    for field in self.hvparam_fields:
                        self.fields[field].initial = hvparam.get(field)
            except AttributeError:
                pass
            
    def clean(self):
        data = self.cleaned_data
        kernel_path = data.get('kernel_path')
        initrd_path = data.get('initrd_path')

        # Makesure if initrd_path is set, kernel_path is aswell
        if initrd_path and not kernel_path:
            msg = u"%s." % _("Kernel Path must be specified along with Initrd Path")
            self._errors['kernel_path'] = self.error_class([msg])
            self._errors['initrd_path'] = self.error_class([msg])
            del data['initrd_path']

        vnc_tls = data.get('vnc_tls')
        vnc_x509_path = data.get('vnc_x509_path')
        vnc_x509_verify = data.get('vnc_x509_verify')

        if not vnc_tls and vnc_x509_path:
            msg = u'%s.' % _('This field can not be set without VNC TLS enabled')
            self._errors['vnc_x509_path'] = self.error_class([msg])
        if vnc_x509_verify and not vnc_x509_path:
            msg = u'%s.' % _('This field is required')
            self._errors['vnc_x509_path'] = self.error_class([msg])

        if self.owner:
            data['start'] = 'reboot' in self.data or self.vm.is_running
            check_quota_modify(self)
            del data['start']

        for i in xrange(data['nic_count']):
            mac_field = 'nic_mac_%s' % i
            link_field = 'nic_link_%s' % i
            mac = data[mac_field] if mac_field in data else None
            link = data[link_field] if link_field in data else None
            if mac and not link:
                self._errors[link_field] = self.error_class([_('This field is required')])
            elif link and not mac:
                self._errors[mac_field] = self.error_class([_('This field is required')])
        data['nic_count_original'] = self.nics

        return data


class HvmModifyVirtualMachineForm(ModifyVirtualMachineForm):
    hvparam_fields = ('boot_order', 'cdrom_image_path', 'nic_type', 
        'disk_type', 'vnc_bind_address', 'acpi', 'use_localtime')
    required = ('disk_type', 'boot_order', 'nic_type')
    empty_field = EMPTY_CHOICE_FIELD
    disk_types = HVM_CHOICES['disk_type']
    nic_types = HVM_CHOICES['nic_type']
    boot_devices = HVM_CHOICES['boot_order']

    acpi = forms.BooleanField(label='ACPI', required=False)
    use_localtime = forms.BooleanField(label='Use Localtime', required=False)
    vnc_bind_address = forms.IPAddressField(label='VNC Bind Address',
        required=False)
    disk_type = forms.ChoiceField(label=_('Disk Type'), choices=disk_types)
    nic_type = forms.ChoiceField(label=_('NIC Type'), choices=nic_types)
    boot_order = forms.ChoiceField(label=_('Boot Device'), choices=boot_devices)

    class Meta(ModifyVirtualMachineForm.Meta):
        exclude = ModifyVirtualMachineForm.Meta.exclude + ('kernel_path', 
            'root_path', 'kernel_args', 'serial_console')

    def __init__(self, vm, *args, **kwargs):
        super(HvmModifyVirtualMachineForm, self).__init__(vm, *args, **kwargs)


class PvmModifyVirtualMachineForm(ModifyVirtualMachineForm):
    hvparam_fields = ('root_path', 'kernel_path', 'kernel_args', 
        'initrd_path')

    initrd_path = forms.CharField(label='initrd Path', required=False)
    kernel_args = forms.CharField(label='Kernel Args', required=False)

    class Meta(ModifyVirtualMachineForm.Meta):
        exclude = ModifyVirtualMachineForm.Meta.exclude + ('disk_type', 
            'nic_type', 'boot_order', 'cdrom_image_path', 'serial_console')

    def __init__(self, vm, *args, **kwargs):
        super(PvmModifyVirtualMachineForm, self).__init__(vm, *args, **kwargs)


class KvmModifyVirtualMachineForm(PvmModifyVirtualMachineForm,
                                  HvmModifyVirtualMachineForm):
    hvparam_fields = ('acpi', 'disk_cache', 'initrd_path', 
        'kernel_args', 'kvm_flag', 'mem_path', 
        'migration_downtime', 'security_domain', 
        'security_model', 'usb_mouse', 'use_chroot', 
        'use_localtime', 'vnc_bind_address', 'vnc_tls', 
        'vnc_x509_path', 'vnc_x509_verify', 'disk_type', 
        'boot_order', 'nic_type', 'root_path', 
        'kernel_path', 'serial_console', 
        'cdrom_image_path',
    )
    disk_caches = HV_DISK_CACHES
    kvm_flags = KVM_FLAGS
    security_models = HV_SECURITY_MODELS
    usb_mice = HV_USB_MICE
    disk_types = KVM_CHOICES['disk_type']
    nic_types = KVM_CHOICES['nic_type']
    boot_devices = KVM_CHOICES['boot_order']

    disk_cache = forms.ChoiceField(label='Disk Cache', required=False,
        choices=disk_caches)
    kvm_flag = forms.ChoiceField(label='KVM Flag', required=False,
        choices=kvm_flags)
    mem_path = forms.CharField(label='Mem Path', required=False)
    migration_downtime = forms.IntegerField(label='Migration Downtime',
        required=False)
    security_model = forms.ChoiceField(label='Security Model',
        required=False, choices=security_models)
    security_domain = forms.CharField(label='Security Domain', required=False)
    usb_mouse = forms.ChoiceField(label='USB Mouse', required=False,
        choices=usb_mice)
    use_chroot = forms.BooleanField(label='Use Chroot', required=False)
    vnc_tls = forms.BooleanField(label='VNC TLS', required=False)
    vnc_x509_path = forms.CharField(label='VNC x509 Path', required=False)
    vnc_x509_verify = forms.BooleanField(label='VNC x509 Verify',
        required=False)
    
    class Meta(ModifyVirtualMachineForm.Meta):
        pass
    
    def __init__(self, vm, *args, **kwargs):
        super(KvmModifyVirtualMachineForm, self).__init__(vm, *args, **kwargs)
        self.fields['disk_type'].choices = self.disk_types
        self.fields['nic_type'].choices = self.nic_types
        self.fields['boot_order'].choices = self.boot_devices
    

class ModifyConfirmForm(forms.Form):

    def clean(self):
        raw = self.data['rapi_dict']
        data = json.loads(raw)

        cleaned = self.cleaned_data
        cleaned['rapi_dict'] = data

        # XXX copy properties into cleaned data so that check_quota_modify can
        # be used
        cleaned['memory'] = data['memory']
        cleaned['vcpus'] = data['vcpus']
        cleaned['start'] = 'reboot' in data or self.vm.is_running
        check_quota_modify(self)

        # Build NICs dicts.  Add changes for existing nics and mark new or
        # removed nics
        #
        # XXX Ganeti only allows a single remove or add but this code will
        # format properly for unlimited adds or removes in the hope that this
        # limitation is removed sometime in the future.
        nics = []
        nic_count_original = data.pop('nic_count_original')
        nic_count = data.pop('nic_count')
        for i in xrange(nic_count):
            nic = dict(link=data.pop('nic_link_%s' % i))
            if 'nic_mac_%s' % i in data:
                nic['mac'] = data.pop('nic_mac_%s' % i)
            index = i if i < nic_count_original else 'add'
            nics.append((index, nic))
        for i in xrange(nic_count_original-nic_count):
            nics.append(('remove',{}))
            try:
                del data['nic_mac_%s' % (nic_count+i)]
            except KeyError:
                pass
            del data['nic_link_%s' % (nic_count+i)]
            
        data['nics'] = nics
        return cleaned


class MigrateForm(forms.Form):
    """ Form used for migrating a Virtual Machine """
    mode = forms.ChoiceField(choices=MODE_CHOICES)
    cleanup = forms.BooleanField(initial=False, required=False,
                                 label=_("Attempt recovery from failed migration"))


class RenameForm(forms.Form):
    """ form used for renaming a Virtual Machine """
    hostname = forms.CharField(label=_('Instance Name'), max_length=255,
                               required=True)
    ip_check = forms.BooleanField(initial=True, required=False, label=_('IP Check'))
    name_check = forms.BooleanField(initial=True, required=False, label=_('DNS Name Check'))

    def __init__(self, vm, *args, **kwargs):
        self.vm = vm
        super(RenameForm, self).__init__(*args, **kwargs)

    def clean_hostname(self):
        data = self.cleaned_data
        hostname = data.get('hostname', None)
        if hostname and hostname == self.vm.hostname:
            raise ValidationError(_("The new hostname must be different than the current hostname"))
        return hostname


class ChangeOwnerForm(forms.Form):
    """ Form used when modifying the owner of a virtual machine """
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), label=_('Owner'))


class ReplaceDisksForm(forms.Form):
    """
    Form used when replacing disks for a virtual machine
    """
    empty_field = EMPTY_CHOICE_FIELD

    MODE_CHOICES = (
        (REPLACE_DISK_AUTO, _('Automatic')),
        (REPLACE_DISK_PRI, _('Replace disks on primary')),
        (REPLACE_DISK_SECONDARY, _('Replace disks secondary')),
        (REPLACE_DISK_CHG, _('Replace secondary with new disk')),
    )

    mode = forms.ChoiceField(choices=MODE_CHOICES, label=_('Mode'))
    disks = forms.MultipleChoiceField(label=_('Disks'), required=False)
    node = forms.ChoiceField(label=_('Node'), choices=[empty_field], required=False)
    iallocator = forms.BooleanField(initial=False, label=_('Iallocator'), required=False)
    
    def __init__(self, instance, *args, **kwargs):
        super(ReplaceDisksForm, self).__init__(*args, **kwargs)
        self.instance = instance

        # set disk choices based on the instance
        disk_choices = [(i, 'disk/%s' % i) for i,v in enumerate(instance.info['disk.sizes'])]
        self.fields['disks'].choices = disk_choices

        # set choices based on the instances cluster
        cluster = instance.cluster
        nodelist = [str(h) for h in cluster.nodes.values_list('hostname', flat=True)]
        nodes = zip(nodelist, nodelist)
        nodes.insert(0, self.empty_field)
        self.fields['node'].choices = nodes

        defaults = cluster_default_info(cluster, get_hypervisor(instance))
        if defaults['iallocator'] != '' :
            self.fields['iallocator'].initial = True
            self.fields['iallocator_hostname'] = forms.CharField(
                                    initial=defaults['iallocator'],
                                    required=False,
                                    widget = forms.HiddenInput())
    
    def clean(self):
        data = self.cleaned_data
        mode = data.get('mode')
        if mode == REPLACE_DISK_CHG:
            iallocator = data.get('iallocator')
            node = data.get('node')
            if not (iallocator or node):
                msg = _('Node or iallocator is required when replacing secondary with new disk')
                self._errors['mode'] = self.error_class([msg])

            elif iallocator and node:
                msg = _('Choose either node or iallocator')
                self._errors['mode'] = self.error_class([msg])
                
        return data

    def clean_disks(self):
        """ format disks into a comma delimited string """
        disks = self.cleaned_data.get('disks')
        if disks is not None:
            disks = ','.join(disks)
        return disks

    def clean_node(self):
        node = self.cleaned_data.get('node')
        return node if node else None

    def save(self):
        """
        Start a replace disks job using the data in this form.
        """
        data = self.cleaned_data
        mode = data['mode']
        disks = data['disks']
        node = data['node']
        if data['iallocator']:
            iallocator = data['iallocator_hostname']
        else:
            iallocator = None
        return self.instance.replace_disks(mode, disks, node, iallocator)
