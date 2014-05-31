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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from django.utils.translation import ugettext as _

from ganeti_webmgr.utils.models import SSHKey


@login_required
def key_get(request, key_id=None, user_id=None):
    if request.is_ajax:
        user = request.user

        if not key_id:
            user_cmp = get_object_or_404(User, pk=user_id) \
                if user_id else user
            form = SSHKeyForm(initial={'user': user_cmp.pk})
        else:
            key_edit = get_object_or_404(SSHKey, pk=key_id)
            form = SSHKeyForm(instance=key_edit)
            user_cmp = key_edit.user

        if not (user.is_superuser or user_cmp == user):
            return HttpResponseForbidden(_("Only superuser or owner "
                                           "can get user's SSH key."))

        return render_to_response("ganeti/ssh_keys/form.html",
                                  {"key_form": form, "key_id": key_id},
                                  context_instance=RequestContext(request))
    return HttpResponse(_("Cannot retrieve information"))


@login_required
def key_save(request, key_id=None):
    if request.is_ajax:
        # get key's user id
        if key_id:
            key_edit = get_object_or_404(SSHKey, pk=key_id)
            owner_id = key_edit.user.id
        else:
            key_edit = SSHKey(user=request.user)
            owner_id = request.user.id

        # check if the user has appropriate permissions
        user = request.user
        if not (user.is_superuser or user.id == owner_id):
            return HttpResponseForbidden(_("Only superuser or owner "
                                           "can save user's SSH key."))

        form = SSHKeyForm(data=request.POST, instance=key_edit)
        if form.is_valid():
            obj = form.save()
            return render_to_response("ganeti/ssh_keys/row.html", {"key": obj},
                                      context_instance=RequestContext(request))
        else:
            return HttpResponse(json.dumps(form.errors),
                                mimetype="application/json")
    return HttpResponse(_("Cannot retrieve information"))


@login_required
def key_delete(request, key_id):
    user = request.user
    key_edit = get_object_or_404(SSHKey, pk=key_id)

    if not (user.is_superuser or key_edit.user == user):
        return HttpResponseForbidden(_('Only superuser or owner '
                                       'can delete user\'s SSH key.'))

    if request.method == "DELETE":
        key_edit.delete()
        return HttpResponse("1", mimetype="application/json")

    return HttpResponse(_("Cannot retrieve information"))


class SSHKeyForm(forms.ModelForm):
    class Meta:
        model = SSHKey

    def __init__(self, *args, **kwargs):
        super(SSHKeyForm, self).__init__(*args, **kwargs)
        self.fields['user'].widget = forms.HiddenInput()

    def clean_key(self):
        value = self.cleaned_data.get('key', None)
        if value is not None:
            value = value.replace('\n', ' ')
        return value
