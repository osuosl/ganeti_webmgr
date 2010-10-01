import json

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext


from object_permissions import get_model_perms, grant, revoke, get_user_perms
from object_permissions.models import UserGroup

def detail(request, id):
    """
    Display organization details
    """
    #TODO permission check
    org = get_object_or_404(UserGroup, id=id)
    return render_to_response("organizations/detail.html", {'org':org}, \
                              context_instance=RequestContext(request))


class UserGroupForm(forms.Form):
    organization = None

    def __init__(self, organization=None, *args, **kwargs):
        self.organization=organization
        super(UserGroupForm, self).__init__(*args, **kwargs)


class UserForm(UserGroupForm):
    """
    Base form for dealing with users
    """
    user = forms.ModelChoiceField(queryset=User.objects.all())


class AddUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is not in organization already """
        user = self.cleaned_data['user']
        if self.organization.users.filter(id=user.id).exists():
            raise forms.ValidationError("User is already a member of this group")
        return user


class RemoveUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is in organization """
        user = self.cleaned_data['user']
        if not self.organization.users.filter(id=user.id).exists():
            raise forms.ValidationError("User is not a member of this group")
        return user


class UserPermissionForm(UserGroupForm):
    """
    Form used for editing permissions
    """
    permissions = forms.MultipleChoiceField(required=False, \
                                            widget=forms.CheckboxSelectMultiple)
    user_id = None

    def __init__(self, user_id, choices=[], *args, **kwargs):
        super(UserPermissionForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.fields['permissions'].choices = choices
    
    def clean(self):
        try:
            user = User.objects.get(id=self.user_id)
            self.cleaned_data['user'] = user
            return self.cleaned_data
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid User")


def add_user(request, id):
    """
    ajax call to add a user to an organization.
    """
    user = request.user
    organization = get_object_or_404(UserGroup, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = AddUserForm(organization, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            organization.users.add(user)
            
            # return html for new user row
            return render_to_response("organizations/user_row.html", \
                                      {'user':user, 'org':organization})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form = AddUserForm()
    return render_to_response("organizations/add_user.html",\
                              {'form':form, 'org':organization}, \
                              context_instance=RequestContext(request))


def remove_user(request, id):
    """
    Ajax call to remove a user from an organization
    """
    user = request.user
    organization = get_object_or_404(UserGroup, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET')

    form = RemoveUserForm(organization, request.POST)
    if form.is_valid():
        user = form.cleaned_data['user']
        organization.users.remove(user)
        
        # return success
        return HttpResponse('1', mimetype='application/json')
        
    # error in form return ajax response
    content = json.dumps(form.errors)
    return HttpResponse(content, mimetype='application/json')


def user_permissions(request, id, user_id):
    """
    Ajax call to update a user's permissions
    """
    user = request.user
    organization = get_object_or_404(UserGroup, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    model_perms = get_model_perms(organization)
    choices = zip(model_perms, model_perms)
    
    if request.method == 'POST':
        form = UserPermissionForm(user_id, choices, organization, request.POST)
        if form.is_valid():
            perms = form.cleaned_data['permissions']
            user = form.cleaned_data['user']
            # update perms - grant all perms selected in the form.  Revoke all
            # other available perms that were not selected.
            for perm in perms:
                grant(user, perm, organization)
            for perm in [p for p in model_perms if p not in perms]:
                revoke(user, perm, organization)
            
            # return html to replace existing user row
            return render_to_response("organizations/user_row.html", {'user':user})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form_user = get_object_or_404(User, id=user_id)
    data = {'permissions':get_user_perms(form_user, organization)}
    form = UserPermissionForm(user_id, choices, data)
    return render_to_response("organizations/permissions.html", \
                              {'form':form, 'org':organization}, \
                              context_instance=RequestContext(request))