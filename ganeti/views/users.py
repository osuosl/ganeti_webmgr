import urllib2
import os
import socket

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from ganeti.models import *

@login_required
def user_list(request):
    user = request.user
    if not user.is_superuser:
        return HttpResponseForbidden('Only a superuser may view all users.')
    
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
        return HttpResponseForbidden('Only a superuser may add a user.')

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
def user_edit(request, user_id=None):
    user = request.user
    if not user.is_superuser:
        return HttpResponseForbidden('Only a superuser may add a user.')

    user_edit = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_edit)
        if form.is_valid():
            data = form.cleaned_data
            form.is_active = data['is_active']
            form.is_superuser = data['is_superuser']
            form.save()
            return HttpResponseRedirect(reverse('user-list'))

    elif request.method == "DELETE":
        user_edit.delete()
        return HttpResponse('1', mimetype='application/json')

    else:
        form = UserEditForm(instance=user_edit)
        
    return render_to_response("users/edit.html", {
            'form':form,
            'username':user_edit,
        },
        context_instance=RequestContext(request),
    )


@login_required
def user_password(request, user_id=None):
    user = request.user
    if not user.is_superuser:
        return HttpResponseForbidden('Only superusers have access to the change \
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
    
    if not form:
        
        form = UserProfileForm(initial={'email':user.email,
                                        'old_password':'',
                                        })
    
    return render_to_response('user_profile.html',
     {"user":request.user, 'form':form},
     context_instance=RequestContext(request))

class UserEditForm(UserChangeForm):
    """
    Form to edit user, based on Auth.UserChangeForm
    """
    
    class Meta(UserChangeForm.Meta):
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'is_active',
            'is_superuser',
        )
    

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