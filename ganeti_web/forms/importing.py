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

from ganeti_web.models import ClusterUser


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
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(),
                                   required=False)


class NodeForm(forms.Form):
    nodes = forms.MultipleChoiceField()

    def __init__(self, choices, *args, **kwargs):
        super(NodeForm, self).__init__(*args, **kwargs)
        self.fields['nodes'].choices = choices
