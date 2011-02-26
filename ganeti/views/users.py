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

import json

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from ganeti.models import SSHKey
from ganeti.views import render_403

@login_required
def user_list(request):
    user = request.user
    if not user.is_superuser:
        return render_403(request, 'Only a superuser may view all users.')
    
    users = User.objects.all()
    
    return render_to_response("users/list.html", {
            'userlist':users
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_add(request):
    user = request.user
    if not user.is_superuser:
        return render_403(request, 'Only a superuser may add a user.')

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_user = User(username=data['username'])
            new_user.set_password(data['password2'])
            new_user.save()
            return HttpResponseRedirect(reverse('user-list'))

    else:
        form = UserCreationForm()

    return render_to_response("users/edit.html", {
            'form':form,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_detail(request, user_id=None):
    user = request.user
    if not user.is_superuser:
        return render_403(request, 'Only a superuser may view a user.')

    user = get_object_or_404(User, id=user_id)
    
    keys = SSHKey.objects.filter(user__pk=user_id).order_by("pk")

    return render_to_response("users/detail.html", {
            'user_detail':user,
            'keyslist': keys,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_edit(request, user_id=None):
    user = request.user
    if not user.is_superuser:
        return render_403(request, 'Only a superuser may edit a user.')

    user_edit = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(data=request.POST, instance=user_edit)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('user-list'))

    elif request.method == "DELETE":
        user_edit.delete()
        return HttpResponse('1', mimetype='application/json')

    else:
        form = UserEditForm(instance=user_edit)
        
    keys = SSHKey.objects.filter(user__pk=user_edit.pk).order_by("pk")
    key_form = SSHKeyForm()

    return render_to_response("users/edit.html", {
            'form':form,
            'username':user_edit,
            'keyslist': keys,
            'key_form': key_form,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_password(request, user_id=None):
    user = request.user
    if not user.is_superuser:
        return render_403(request, 'Only superusers have access to the change \
                                     password form.')

    user_edit = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = SetPasswordForm(user=user_edit, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('user-list'))
    else:
        form = SetPasswordForm(user=user_edit)
    
    return render_to_response("users/password.html", {
            'form':form,
            'username':user_edit,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_profile(request):
    """
    Form for editing a User's Profile
    """
    form = None
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        form.user = user
        if form.is_valid():
            data = form.cleaned_data
            user.email = data['email']
            if data['new_password']:
                user.set_password(data['new_password'])
            user.save()
            user.get_profile().save()
            form = None
            messages.add_message(request, messages.SUCCESS,
                                 'Saved successfully')
    
    if not form:
        
        form = UserProfileForm(initial={'email':user.email,
                                        'old_password':'',
                                        })
    
    keys = SSHKey.objects.filter(user__pk=user.pk).order_by("pk")
    key_form = SSHKeyForm()

    return render_to_response('user_profile.html',
    {"user":request.user, 'form':form, 'keyslist':keys, 'key_form':key_form},
     context_instance=RequestContext(request))



@login_required
def key_get(request, key_id=None):
    if request.is_ajax:
        user = request.user
        form, user_cmp = None, request.user
        if not key_id:
            form = SSHKeyForm()
        else:
            key_edit = get_object_or_404(SSHKey, pk=key_id)
            form = SSHKeyForm(instance=key_edit)
            user_cmp = key_edit.user
        if not (user.is_superuser or user_cmp==user):
            return HttpResponseForbidden("Only superuser or owner can get user's SSH key.")
        
        return render_to_response("ssh_keys/form.html", {"key_form": form,
                    "key_id":key_id}, context_instance=RequestContext(request))
    return HttpResponse("Cannot retrieve information")


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
        if not (user.is_superuser or user.id==owner_id):
            return HttpResponseForbidden("Only superuser or owner can save user's SSH key.")

        form = SSHKeyForm(data=request.POST, instance=key_edit)
        if form.is_valid():
            obj = form.save()
            return render_to_response("ssh_keys/row.html", {"key": obj},
                                      context_instance=RequestContext(request))
        else:
            return HttpResponse(json.dumps(form.errors),
                                mimetype="application/json")
    return HttpResponse("Cannot retrieve information")


@login_required
def key_delete(request, key_id):
    user = request.user
    key_edit = get_object_or_404(SSHKey, pk=key_id)

    if not (user.is_superuser or key_edit.user==user):
        return HttpResponseForbidden('Only superuser or owner can delete user\'s SSH key.')

    if request.method == "DELETE":
        key_edit.delete()
        return HttpResponse("1", mimetype="application/json")

    return HttpResponse("Cannot retrieve information")


class SSHKeyForm(forms.ModelForm):
    class Meta:
        model = SSHKey
        exclude = ("user", )

    def clean_key(self):
        value = self.cleaned_data.get('key', None)
        if value is not None:
            value = value.replace('\n',' ')
        return value


class UserEditForm(UserChangeForm):
    """
    Form to edit user, based on Auth.UserChangeForm
    """

    new_password1 = forms.CharField(label='New password',
                                    widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label='Confirm password',
                                    widget=forms.PasswordInput, required=False)
    
    class Meta(UserChangeForm.Meta):
        fields = (
            'username',
            #'first_name',
            #'last_name',
            'email',
            'is_active',
            'is_superuser',
        )

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
    
    def clean_new_password2(self):
        password2 = self.cleaned_data.get('new_password2')
        if self.cleaned_data.get('new_password1') != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        password1 = self.cleaned_data.get('new_password1')
        if password1 and self.cleaned_data.get('new_password2'):
            self.instance.set_password(password1)
        return super(UserEditForm, self).save(commit)


class UserProfileForm(forms.Form):
    """
    Form for editing a User's Profile
    """
    email = forms.EmailField()
    old_password = forms.CharField(required=False, widget=forms.PasswordInput)
    new_password = forms.CharField(required=False, widget=forms.PasswordInput)
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput)

    # needed to verify the user's password
    user = None

    def clean(self):
        """
        Overridden to add password change verification
        """
        data = self.cleaned_data
        old = data.get('old_password', None)
        new = data.get('new_password', None)
        confirm = data.get('confirm_password', None)
        
        if new or confirm:
            if not self.user.check_password(old):
                del data['old_password']
                msg = 'Old Password is incorrect'
                self._errors['old_password'] = self.error_class([msg])
            
            if not new:
                if 'new_password' in data: del data['new_password']
                msg = 'Enter a new password'
                self._errors['new_password'] = self.error_class([msg])
            
            if not confirm:
                if 'confirm_password' in data: del data['confirm_password']
                msg = 'Confirm new password'
                self._errors['confirm_password'] = self.error_class([msg])
            
            if new and confirm and new != confirm:
                del data['new_password']
                del data['confirm_password']
                msg = 'New passwords do not match'
                self._errors['new_password'] = self.error_class([msg])
        
        return data
