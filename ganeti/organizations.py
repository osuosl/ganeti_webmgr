import json

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render_to_response

from ganeti.models import Organization
from object_permissions import get_model_perms, grant

def detail(request, id):
    """
    Display organization details
    """
    #TODO permission check
    
    org = get_object_or_404(Organization, id=id)
    return render_to_response("organizations/detail.html", {'org':org})


class UserForm(forms.Form):
    """
    Base form for dealing with users
    """
    user = forms.ModelChoiceField(queryset=User.objects.all())
    organization = None

    def __init__(self, organization=None, *args, **kwargs):
        self.organization=organization
        super(UserForm, self).__init__(*args, **kwargs)


class AddUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is not in organization already """
        user = self.cleaned_data['user']
        if self.organization.users.filter(user=user).exists():
            raise forms.ValidationError("User is already a member of this group")
        return user


class RemoveUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is in organization """
        user = self.cleaned_data['user']
        if not self.organization.users.filter(user=user).exists():
            raise forms.ValidationError("User is not a member of this group")
        return user


class UserPermissionForm(UserForm):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField()

    def __init__(self, choices=[], *args, **kwargs):
        super(UserPermissionForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].choices = choices

def add_user(request, id):
    """
    ajax call to add a user to an organization.
    """
    user = request.user
    organization = get_object_or_404(Organization, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = AddUserForm(organization, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            organization.users.add(user.get_profile())
            
            # return html for new user row
            return render_to_response("organizations/user_row.html", {'user':user})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form = AddUserForm()
    return render_to_response("organizations/add_user.html", {'form':form})


def remove_user(request, id):
    """
    Ajax call to remove a user from an organization
    """
    user = request.user
    organization = get_object_or_404(Organization, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET')

    form = RemoveUserForm(organization, request.POST)
    if form.is_valid():
        user = form.cleaned_data['user']
        organization.users.remove(user.get_profile())
        
        # return success
        return HttpResponse('1', mimetype='application/json')
        
    # error in form return ajax response
    content = json.dumps(form.errors)
    return HttpResponse(content, mimetype='application/json')


def update_user(request, id):
    """
    Ajax call to update a user's permissions
    """
    user = request.user
    organization = get_object_or_404(Organization, id=id)
    perms = get_model_perms(organization)
    choices = zip(perms, perms)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = UserPermissionForm(choices, organization, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            perms = form.cleaned_data['permissions']
            for perm in perms:
                grant(user, perm, organization)
            
            # return html to replace existing user row
            return render_to_response("organizations/user_row.html", {'user':user})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form = UserPermissionForm(choices)
    return render_to_response("organizations/permissions.html", {'form':form})