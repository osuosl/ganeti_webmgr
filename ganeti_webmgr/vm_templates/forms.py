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

from django.forms import Form, CharField, ModelChoiceField, ValidationError
from django.utils.translation import ugettext_lazy as _

from ganeti_webmgr.authentication.models import ClusterUser


class VirtualMachineTemplateCopyForm(Form):
    """
    Form used to when copying a VirtualMachineTemplate
    """
    template_name = CharField(label=_('Template Name'), max_length=255)
    description = CharField(label=_('Description'), max_length=255,
                            required=False)


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


class TemplateFromVMInstance(Form):
    template_name = CharField(label=_("Template Name"), max_length=255)

    def clean_template_name(self):
        name = self.cleaned_data['template_name']
        if name.strip(' ') == '':
            raise ValidationError(_("Name cannot consist of spaces."))
        return name
