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


from django import forms
from django.forms import ValidationError

from ganeti import constants
from ganeti.fields import DataVolumeField
from ganeti.models import Cluster, ClusterUser, Organization, \
    VirtualMachineTemplate, VirtualMachine
from ganeti.utilities import cluster_default_info, cluster_os_list

FQDN_RE = r'(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)'

class NewVirtualMachineForm(forms.ModelForm):
    """
    Virtual Machine Creation form
    """
    empty_field = constants.EMPTY_CHOICE_FIELD
    templates = constants.KVM_DISK_TEMPLATES
    disktypes = constants.KVM_DISK_TYPES
    nicmodes = constants.KVM_NIC_MODES
    nictypes = constants.KVM_NIC_TYPES
    bootchoices = constants.KVM_BOOT_ORDER

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
    memory = DataVolumeField(label='Memory', min_value=100)
    disk_size = DataVolumeField(label='Disk Size', min_value=100)
    disk_type = forms.ChoiceField(label='Disk Type', choices=disktypes)
    nic_mode = forms.ChoiceField(label='NIC Mode', choices=nicmodes)
    nic_type = forms.ChoiceField(label='NIC Type', choices=nictypes)
    boot_order = forms.ChoiceField(label='Boot Device', choices=bootchoices)

    class Meta:
        model = VirtualMachineTemplate
        exclude = ('template_name')

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
            nodelist = [str(h) for h in cluster.nodes.values_list('hostname', flat=True)]
            nodes = zip(nodelist, nodelist)
            nodes.insert(0, self.empty_field)
            oslist.insert(0, self.empty_field)
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
            self.fields['memory'].initial = defaults['memory']
            self.fields['disk_type'].initial = defaults['disk_type']
            self.fields['root_path'].initial = defaults['root_path']
            self.fields['kernel_path'].initial = defaults['kernel_path']
            self.fields['serial_console'].initial = defaults['serial_console']
            self.fields['nic_link'].initial = defaults['nic_link']

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
                        msg = "Owner cannot be changed when recovering a failed deployment"
                        self._errors["owner"] = self.error_class([msg])
                else:
                    raise ValidationError("Hostname is already in use for this cluster")

            except VirtualMachine.DoesNotExist:
                # doesn't exist, no further checks needed
                pass

        return hostname

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
                        (used['ram'] + data['memory']) > quota['ram']:
                            del data['memory']
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
        boot_order = data.get('boot_order', '')
        image_path = data.get('cdrom_image_path', '')
        if boot_order == 'cdrom':
            if image_path == '':
                msg = u'Image path required if boot device is CD-ROM.'
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
                msg = u'Automatic Allocation was selected, but there is no \
                      IAllocator available.'
                self._errors['iallocator'] = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return data


class ModifyVirtualMachineForm(NewVirtualMachineForm):
    """
    Simple way to modify a virtual machine instance.
    """
    # Fields to be excluded from parent.
    exclude = ('start', 'owner', 'cluster', 'hostname', 'name_check',
        'iallocator', 'iallocator_hostname', 'disk_template', 'pnode', 'snode',\
        'disk_size', 'nic_mode', 'template_name')
    # Fields that should be required.
    required = ('vcpus', 'memory', 'disk_type', 'boot_order', \
        'nic_type', 'root_path')

    disk_caches = constants.KVM_DISK_CACHES
    security_models = constants.KVM_SECURITY_MODELS
    kvm_flags = constants.KVM_FLAGS
    usb_mice = constants.KVM_USB_MICE

    acpi = forms.BooleanField(label='ACPI', required=False)
    disk_cache = forms.ChoiceField(label='Disk Cache', required=False, \
        choices=disk_caches)
    initrd_path = forms.CharField(label='initrd Path', required=False)
    kernel_args = forms.CharField(label='Kernel Args', required=False)
    kvm_flag = forms.ChoiceField(label='KVM Flag', required=False, \
        choices=kvm_flags)
    mem_path = forms.CharField(label='Mem Path', required=False)
    migration_downtime = forms.IntegerField(label='Migration Downtime', \
        required=False)
    nic_mac = forms.CharField(label='NIC Mac', required=False)
    security_model = forms.ChoiceField(label='Security Model', \
        required=False, choices=security_models)
    security_domain = forms.CharField(label='Security Domain', required=False)
    usb_mouse = forms.ChoiceField(label='USB Mouse', required=False, \
        choices=usb_mice)
    use_chroot = forms.BooleanField(label='Use Chroot', required=False)
    use_localtime = forms.BooleanField(label='Use Localtime', required=False)
    vnc_bind_address = forms.IPAddressField(label='VNC Bind Address', \
        required=False)
    vnc_tls = forms.BooleanField(label='VNC TLS', required=False)
    vnc_x509_path = forms.CharField(label='VNC x509 Path', required=False)
    vnc_x509_verify = forms.BooleanField(label='VNC x509 Verify', \
        required=False)

    class Meta:
        model = VirtualMachineTemplate

    def __init__(self, user, cluster, initial=None, *args, **kwargs):
        super(ModifyVirtualMachineForm, self).__init__(user, cluster=cluster, \
                initial=initial, *args, **kwargs)
        # Remove all fields in the form that are not required to modify the 
        #   instance.
        for field in self.exclude:
            del self.fields[field]
    
        # Make sure certain fields are required
        for field in self.required:
            self.fields[field].required = True

    def clean_initrd_path(self):
        data = self.cleaned_data['initrd_path']
        if data != '' and \
            (not data.startswith('/') and data != 'no_initrd_path'):
            msg = u'This field must start with a "/".'
            self._errors['initrd_path'] = self.error_class([msg])
        return data

    def clean_security_domain(self):
        data = self.cleaned_data['security_domain']
        security_model = self.cleaned_data['security_model']
        msg = None

        if data and security_model != 'user': 
            msg = u'This field can not be set if Security Mode \
                is not set to User.'
        elif security_model == 'user':
            if not data:
                msg = u'This field is required.'
            elif not data[0].isalpha():
                msg = u'This field must being with an alpha character.'

        if msg:
            self._errors['security_domain'] = self.error_class([msg])
        return data

    def clean_vnc_x509_path(self):
        data = self.cleaned_data['vnc_x509_path']
        if data and not data.startswith('/'):
            msg = u'This field must start with a "/".' 
            self._errors['vnc_x509_path'] = self.error_class([msg])
        return data

    def clean(self):
        data = self.cleaned_data
        kernel_path = data.get('kernel_path')
        initrd_path = data.get('initrd_path')

        # Makesure if initrd_path is set, kernel_path is aswell
        if initrd_path and not kernel_path:
            msg = u"Kernel Path must be specified along with Initrd Path."
            self._errors['kernel_path'] = self.error_class([msg])
            self._errors['initrd_path'] = self.error_class([msg])
            del data['initrd_path']

        vnc_tls = data.get('vnc_tls')
        vnc_x509_path = data.get('vnc_x509_path')
        vnc_x509_verify = data.get('vnc_x509_verify')
    
        if not vnc_tls and vnc_x509_path:
            msg = u'This field can not be set without VNC TLS enabled.'
            self._errors['vnc_x509_path'] = self.error_class([msg])
        if vnc_x509_verify and not vnc_x509_path:
            msg = u'This field is required.'
            self._errors['vnc_x509_path'] = self.error_class([msg])

        return data


class ModifyConfirmForm(forms.Form):
    pass


class MigrateForm(forms.Form):
    """ Form used for migrating a Virtual Machine """
    mode = forms.ChoiceField(choices=constants.MODE_CHOICES)
    cleanup = forms.BooleanField(initial=False, required=False,
                                 label="Attempt recovery from failed migration")


class RenameForm(forms.Form):
    """ form used for renaming a Virtual Machine """
    hostname = forms.RegexField(label='Instance Name', regex=FQDN_RE,
                            error_messages={
                                'invalid': 'Instance name must be resolvable',
                            },
                            max_length=255, required=True)
    ip_check = forms.BooleanField(initial=True, required=False, label='IP Check')
    name_check = forms.BooleanField(initial=True, required=False, label='DNS Name Check')

    def __init__(self, vm, *args, **kwargs):
        self.vm = vm
        super(RenameForm, self).__init__(*args, **kwargs)

    def clean_hostname(self):
        data = self.cleaned_data
        hostname = data.get('hostname', None)
        if hostname and hostname == self.vm.hostname:
            raise ValidationError("The new hostname must be different than the current hostname")
        return hostname
