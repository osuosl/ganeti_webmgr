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
from django.forms import Form, CharField, ModelChoiceField, ValidationError
from django.utils.translation import ugettext_lazy as _

from ganeti_web.forms.virtual_machine import (VirtualMachineForm,
                                              NewVirtualMachineForm)
from ganeti_web.models import Cluster, ClusterUser, VirtualMachine
from ganeti_web.utilities import cluster_default_info, cluster_os_list



class VirtualMachineTemplateForm(NewVirtualMachineForm):
    """
    Form to edit/create VirtualMachineTemplates
    """
    cluster = forms.ModelChoiceField(queryset=Cluster.objects.none(), label=_('Cluster'))
    disk_count = forms.IntegerField(initial=0,  widget=forms.HiddenInput())
    nic_count = forms.IntegerField(initial=0, widget=forms.HiddenInput())

    class Meta(VirtualMachineForm.Meta):
        exclude = ('pnode','snode','iallocator','iallocator_hostname',
            'owner', 'hypervisor', 'hostname')
        required = ('template_name', 'cluster')

    def __init__(self, *args, **kwargs):
        """
        Initialize VirtualMachineTemplateForm
        """
        cluster = None
        disk_count = 1
        nic_count = 1
        initial = kwargs.get('initial', None)
        user = kwargs.pop('user', None)

        super(VirtualMachineForm, self).__init__(*args, **kwargs)

        if not initial:
            initial = dict(self.data.items())

        if initial:
            if initial.get('cluster', None):
                try:
                    cluster = Cluster.objects.get(pk=initial['cluster'])
                except Cluster.DoesNotExist:
                    # defer to clean function to return errors
                    pass

            # Load disks and nics.
            if 'disks' in initial and not 'disk_count' in initial: 
                disks = initial['disks']
                disk_count = len(disks)
                self.create_disk_fields(disk_count)
                for i, disk in enumerate(disks):
                    self.fields['disk_size_%s' % i].initial = disk['size']
            else:
                disk_count = int(initial['disk_count'])
                self.create_disk_fields(disk_count)
                for i in xrange(disk_count):
                    self.fields['disk_size_%s' %i].initial = initial['disk_size_%s'%i]

            if 'nics' in initial:
                nics = initial['nics']
                nic_count = len(nics)
                self.create_nic_fields(nic_count)
                for i, nic in enumerate(nics):
                    self.fields['nic_mode_%s' % i].initial = nic['mode']
                    self.fields['nic_link_%s' % i].initial = nic['link']
            else:
                nic_count = int(initial['nic_count'])
                self.create_nic_fields(nic_count)
                for i in xrange(nic_count):
                    self.fields['nic_mode_%s' % i].initial = initial['nic_mode_%s'%i]
                    self.fields['nic_link_%s' % i].initial = initial['nic_link_%s'%i]

       
        if cluster and hasattr(cluster, 'info'):
            # Get choices based on hypervisor passed to the form.
            hv = initial.get('hypervisor', None)
            if hv:
                defaults = cluster_default_info(cluster, hv)
            else:
                defaults = cluster_default_info(cluster)
                hv = defaults['hypervisor']
            # Set field choices and hypervisor
            if hv == 'kvm' or hv == 'xen-hvm':
                self.fields['nic_type'].choices = defaults['nic_types']
                self.fields['disk_type'].choices = defaults['disk_types']
                self.fields['boot_order'].choices = defaults['boot_devices']

            # Set os choices
            oslist = cluster_os_list(cluster)
            oslist.insert(0, self.empty_field)
            self.fields['os'].choices = oslist
        
        if not initial:
            self.create_disk_fields(disk_count)
            self.create_nic_fields(nic_count)

        # Set cluster choices
        if user.is_superuser:
            clusters = Cluster.objects.all()
        else:
            clusters = user.get_objects_any_perms(Cluster, ['admin','create_vm'])

        self.fields['cluster'].queryset = clusters

        # XXX Remove fields explicitly set in NewVirtualMachineForm
        #  Django ticket #8620
        for field in self.Meta.exclude:
            if field in self.fields.keys():
                del self.fields[field]
        for field in self.fields:
            if field not in self.Meta.required:
                self.fields[field].required = False
            else:
                self.fields[field].required = True

    def clean_template_name(self):
        name = self.cleaned_data['template_name']
        if name.strip(' ') == '':
            raise forms.ValidationError(_("Name cannot consist of spaces."))
        return name

    def clean(self):
        data = self.cleaned_data

        disk_count = data.get('disk_count', 0)
        # sum disk sizes and build disks param for input into ganeti
        disk_sizes= []
        if disk_count > 0:
            x = lambda y: data.get('disk_size_%s' % y)
            # Ignore empty disk fields
            disk_sizes = [ x(i) for i in xrange(disk_count) if x(i) != None]
        disk_size = sum(disk_sizes)
        data['disk_size'] = disk_size
        data['disks'] = [dict(size=size) for size in disk_sizes]

        # build nics dictionaries
        nic_count = data.get('nic_count', 0)
        nics = []
        if nic_count > 0:
            for i in xrange(data.get('nic_count',0)):
                nics.append(dict(mode=data.get('nic_mode_%s' % i),
                                 link=data.get('nic_link_%s' % i)))
        data['nics'] = nics
        return data


class VirtualMachineTemplateCopyForm(forms.Form):
    """
    Form used to when copying a VirtualMachineTemplate
    """
    template_name = forms.CharField(label=_('Template Name'), max_length=255)
    description = forms.CharField(label=_('Description'), max_length=255, required=False)



class VMInstanceFromTemplate(Form):
    owner = ModelChoiceField(label=_('Owner'),
                             queryset=ClusterUser.objects.all(),
                             empty_label=None)
    hostname = CharField(label=_('Instance Name'), max_length=255)


    def clean_hostname(self):
        hostname = self.cleaned_data.get('hostname')

        # Spaces in hostname will always break things.
        if ' ' in hostname:
            self.errors["hostname"] = self.error_class(
                ["Hostnames cannot contain spaces."])
        return hostname
