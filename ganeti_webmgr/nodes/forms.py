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
from django.forms import ValidationError
from django.utils.translation import ugettext as _

from ganeti_webmgr.ganeti_web import constants
from ganeti_webmgr.utils import cluster_default_info


class RoleForm(forms.Form):
    """
    Form for editing roles
    """
    role = forms.ChoiceField(initial='',
                             choices=constants.ROLE_CHOICES,
                             label='New Role')
    force = forms.BooleanField(initial=False, required=False)


class MigrateForm(forms.Form):
    """ Form used for migrating primary Virtual Machines off a Node """
    mode = forms.ChoiceField(choices=constants.MODE_CHOICES)


class EvacuateForm(forms.Form):
    EMPTY_FIELD = constants.EMPTY_CHOICE_FIELD

    iallocator = forms.BooleanField(initial=False, required=False,
                                    label='Automatic Allocation')
    iallocator_hostname = forms.CharField(initial='', required=False,
                                          widget=forms.HiddenInput())
    node = forms.ChoiceField(initial='', choices=[EMPTY_FIELD], required=False)

    def __init__(self, cluster, node, *args, **kwargs):
        super(EvacuateForm, self).__init__(*args, **kwargs)

        node_list = [str(h) for h in cluster.nodes.exclude(pk=node.pk)
                     .values_list('hostname', flat=True)]
        nodes = zip(node_list, node_list)
        nodes.insert(0, self.EMPTY_FIELD)
        self.fields['node'].choices = nodes

        defaults = cluster_default_info(cluster)
        if defaults['iallocator'] != '':
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
            raise ValidationError(_('Must choose automatic allocation '
                                    'or a specific node'))

        return data
