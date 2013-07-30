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
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from utils.fields import DataVolumeField
from clusters.models import Cluster
from authentication.models import ClusterUser


class QuotaForm(forms.Form):
    """
    Form for editing user quota on a cluster
    """
    input = forms.TextInput(attrs={'size': 5})

    user = forms.ModelChoiceField(queryset=ClusterUser.objects.all(),
                                  widget=forms.HiddenInput)
    ram = DataVolumeField(label='Memory', required=False, min_value=0)
    virtual_cpus = forms.IntegerField(label='Virtual CPUs', required=False,
                                      min_value=0, widget=input)
    disk = DataVolumeField(label='Disk Space', required=False, min_value=0)
    delete = forms.BooleanField(required=False, widget=forms.HiddenInput)


class EditClusterForm(forms.ModelForm):
    """
    Basic form for editing a cluster.
    """

    class Meta:
        model = Cluster
        widgets = {
            'password': forms.PasswordInput(),
        }

    ram = DataVolumeField(label=_('Memory'), required=False, min_value=0)
    disk = DataVolumeField(label=_('Disk Space'), required=False, min_value=0)

    def need_username(self):
        msg = _('Enter a username')
        self._errors['username'] = self.error_class([msg])

    def need_password(self):
        msg = _('Enter a password')
        self._errors['password'] = self.error_class([msg])

    def clean(self):
        """
        Validate this form.

        Much of the validation is handled in the Cluster model; this method
        should not duplicate any validation done as part of the Cluster model
        definition.
        """

        data = self.cleaned_data = super(EditClusterForm, self).clean()

        # Automatically set the slug on cluster creation, based on the
        # hostname, if no slug was provided.
        if "hostname" in data and 'slug' not in data:
            data['slug'] = slugify(data["hostname"].split('.')[0])
            del self._errors['slug']

        username = data.get('username', "")
        password = data.get('password', "")

        if self.instance is None or not self.instance.username:
            # This is a new cluster, or a cluster without a username.
            if username and not password:
                self.need_password()
            elif password and not username:
                self.need_username()

        elif self.instance.username:
            # The cluster had a username set. Password is not required unless
            # the username has changed.
            if username and not password:
                if username == self.instance.username:
                    # The user didn't enter a password and it wasn't required;
                    # retain the existing password instead of setting it to
                    # the empty string.
                    data['password'] = self.instance.password
                else:
                    # New username; get a new password too.
                    self.need_password()

            elif password and not username:
                self.need_username()

        return data
