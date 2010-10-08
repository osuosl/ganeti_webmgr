import json

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions import get_model_perms, grant, revoke, get_user_perms
from object_permissions.models import UserGroup
from object_permissions.views.permissions import ObjectPermissionForm


class UserGroupForm(forms.ModelForm):
    """
    Form for editing UserGroups
    """
    class Meta:
        model = UserGroup


class UserForm(forms.Form):
    """
    Base form for dealing with users
    """
    user_group = None
    user = forms.ModelChoiceField(queryset=User.objects.all())
    
    def __init__(self, user_group=None, *args, **kwargs):
        self.user_group=user_group
        super(UserForm, self).__init__(*args, **kwargs)


class AddUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is not in user_group already """
        user = self.cleaned_data['user']
        if self.user_group.users.filter(id=user.id).exists():
            raise forms.ValidationError("User is already a member of this group")
        return user


class RemoveUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is in user_group """
        user = self.cleaned_data['user']
        if not self.user_group.users.filter(id=user.id).exists():
            raise forms.ValidationError("User is not a member of this group")
        return user


@login_required
def list(request):
    """
    List all user groups.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    groups = UserGroup.objects.all()
    return render_to_response("user_group/list.html", \
                              {'groups':groups}, \
                              context_instance=RequestContext(request)) 


@login_required
def detail(request, id=None):
    """
    Display user_group details
    
    @param id: id of UserGroup
    """
    group = get_object_or_404(UserGroup, id=id) if id else None
    user = request.user
    
    if not (user.is_superuser or user.has_perm('admin', group)):
        return HttpResponseForbidden()
    
    method = request.method
    if method == 'GET':
        return render_to_response("user_group/detail.html", {'group':group}, \
                              context_instance=RequestContext(request))
    
    elif method == 'POST':
        if request.POST:
            # form data, this was a submission
            form = UserGroupForm(request.POST, instance=group)
            if form.is_valid():
                group = form.save()
                return render_to_response("user_group/group_row.html", \
                        {'group':group}, \
                        context_instance=RequestContext(request))
            
            content = json.dumps(form.errors)
            return HttpResponse(content, mimetype='application/json')
        
        else:
            form = UserGroupForm(instance=group)
        
        return render_to_response("user_group/edit.html", \
                        {'group':group, 'form':form}, \
                        context_instance=RequestContext(request))
    
    elif method == 'DELETE':
        group.delete()
        return HttpResponse('1', mimetype='application/json')

    return HttpResponseNotAllowed(['PUT', 'HEADER'])


@login_required
def add_user(request, id):
    """
    ajax call to add a user to a UserGroup
    
    @param id: id of UserGroup
    """
    user = request.user
    user_group = get_object_or_404(UserGroup, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', user_group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = AddUserForm(user_group, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            user_group.users.add(user)
            
            # return html for new user row
            return render_to_response("user_group/user_row.html", \
                                      {'user':user, 'group':user_group})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form = AddUserForm()
    return render_to_response("user_group/add_user.html",\
                              {'form':form, 'group':user_group}, \
                              context_instance=RequestContext(request))


@login_required
def remove_user(request, id):
    """
    Ajax call to remove a user from an UserGroup
    
    @param id: id of UserGroup
    """
    user = request.user
    user_group = get_object_or_404(UserGroup, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', user_group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET')

    form = RemoveUserForm(user_group, request.POST)
    if form.is_valid():
        user = form.cleaned_data['user']
        user_group.users.remove(user)
        user.revoke_all(user_group)
        
        # return success
        return HttpResponse('1', mimetype='application/json')
        
    # error in form return ajax response
    content = json.dumps(form.errors)
    return HttpResponse(content, mimetype='application/json')


@login_required
def user_permissions(request, id):
    """
    Ajax call to update a user's permissions
    
    @param id: id of UserGroup
    """
    user = request.user
    user_group = get_object_or_404(UserGroup, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', user_group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = ObjectPermissionForm(user_group, request.POST)
        if form.is_valid():
            form.update_perms()
            user = form.cleaned_data['user']
            
            # return html to replace existing user row
            return render_to_response("user_group/user_row.html", \
                                      {'group':user_group, 'user':user})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')
    
    if 'user' not in request.GET:
        return HttpResponseNotFound()
    
    # render a form for an existing user only
    user_id = request.GET['user']
    form_user = get_object_or_404(User, id=user_id)
    data = {'permissions':get_user_perms(form_user, user_group), 'user':user_id}
    form = ObjectPermissionForm(user_group, data)
    return render_to_response("user_group/permissions.html", \
                        {'form':form, 'group':user_group, 'user_id':user_id}, \
                        context_instance=RequestContext(request))