import json

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, \
    HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions.signals import view_add_user, view_remove_user

from ganeti_webmgr.muddle_users.signals import (view_group_edited, view_group_created,
                                  view_group_deleted)


class GroupForm(forms.ModelForm):
    """
    Form for editing Groups
    """
    class Meta:
        model = Group


class UserForm(forms.Form):
    """
    Base form for dealing with users
    """
    group = None
    user = forms.ModelChoiceField(queryset=User.objects.all())
    
    def __init__(self, group=None, *args, **kwargs):
        self.group=group
        super(UserForm, self).__init__(*args, **kwargs)


class AddUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is not in group already """
        user = self.cleaned_data['user']
        if self.group.user_set.filter(id=user.id).exists():
            raise forms.ValidationError("User is already a member of this group")
        return user


class RemoveUserForm(UserForm):
    def clean_user(self):
        """ Validate that user is in group """
        user = self.cleaned_data['user']
        if not self.group.user_set.filter(id=user.id).exists():
            raise forms.ValidationError("User is not a member of this group")
        return user


@login_required
def list(request, template='group/list.html'):
    """
    List all user groups.
    """
    user = request.user
    if request.user.is_superuser:
        groups = Group.objects.all()
    else:
        groups = user.get_objects_any_perms(Group, ['admin'])
        if not groups:
            return HttpResponseForbidden()

    return render_to_response(template,
                              {'groups':groups},
                              context_instance=RequestContext(request)) 


@login_required
def detail(request, id=None, template='group/detail.html'):
    """
    Display group details
    
    @param id: id of Group
    """
    group = get_object_or_404(Group, id=id) if id else None
    user = request.user
    
    if not (user.is_superuser or user.has_perm('admin', group)):
        return HttpResponseForbidden()
    
    return render_to_response(template,
                        {'object':group,
                         'group':group,
                         'users':group.user_set.all(),
                         'url':reverse('group-permissions', args=[id])
                         },
                          context_instance=RequestContext(request))


@login_required
def edit(request, id=None, template="group/edit.html"):
    """
    Edit a group

    @param id: id of group to edit, or None for a new group
    @param template: template used for rendering a form
    """
    group = get_object_or_404(Group, id=id) if id else None
    user = request.user

    if not (user.is_superuser or user.has_perm('admin', group)):
        return HttpResponseForbidden()

    method = request.method
    if method == 'POST':
            # form data, this was a submission
            form = GroupForm(request.POST, instance=group)
            if form.is_valid():
                group = form.save()
                if not id:
                    view_group_created.send(sender=group, editor=user)
                else:
                    view_group_edited.send(sender=group, editor=user)

                return HttpResponseRedirect(group.get_absolute_url())
            
    elif method == 'DELETE':
        group.delete()
        view_group_deleted.send(sender=group, editor=user)
        return HttpResponse('1', mimetype='application/json')

    else:
        form = GroupForm(instance=group)

    return render_to_response(template, {
            'form':form,
            'group':group,
        },
        context_instance=RequestContext(request),
    )


@login_required
def add_user(request, id, user_row_template='group/user_row.html'):
    """
    ajax call to add a user to a Group
    
    @param id: id of Group
    """
    editor = request.user
    group = get_object_or_404(Group, id=id)
    
    if not (editor.is_superuser or editor.has_perm('admin', group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = AddUserForm(group, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            group.user_set.add(user)
            
            # signal
            view_add_user.send(sender=editor, user=user, obj=group)
            
            # return html for new user row
            url = reverse('group-permissions', args=[id])
            return render_to_response(
                user_row_template,
                        {'user_detail':user, 'object':group, 'url':url},
                        context_instance=RequestContext(request))
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    form = AddUserForm()
    return render_to_response("group/add_user.html",
                              {'form':form, 'group':group},
                              context_instance=RequestContext(request))


@login_required
def remove_user(request, id):
    """
    Ajax call to remove a user from an Group
    
    @param id: id of Group
    """
    editor = request.user
    group = get_object_or_404(Group, id=id)
    
    if not (editor.is_superuser or editor.has_perm('admin', group)):
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method != 'POST':
        return HttpResponseNotAllowed('GET')

    form = RemoveUserForm(group, request.POST)
    if form.is_valid():
        user = form.cleaned_data['user']
        group.user_set.remove(user)
        user.revoke_all(group)
        
        # signal
        view_remove_user.send(sender=editor, user=user, obj=group)
        
        # return success
        return HttpResponse('1', mimetype='application/json')
        
    # error in form return ajax response
    content = json.dumps(form.errors)
    return HttpResponse(content, mimetype='application/json')
