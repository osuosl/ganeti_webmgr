import json

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response

from ganeti.models import Organization


def detail(request, id):
    """
    Display organization details
    """
    #TODO permission check
    
    org = get_object_or_404(Organization, id=id)
    return render_to_response("organization.html", {'org':org})


class AddUserForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())


def add_user(request, id):
    """
    ajax call to add a user to an organization.
    """
    user = request.user
    organization = get_object_or_404(Organization, id=id)
    
    if not (user.is_superuser or user.has_perm('admin', organization)):
        print user.has_perm('admin', organization)
        return HttpResponseForbidden('You do not have sufficient privileges')
    
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user']
            user = User.objects.get(id=user_id)
            
            # return html for new user row
            return render_to_response("user_row.html", {'user':user})
        
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
    
    if request.method == 'GET':
        return HttpResponseNotAllowed('GET')


def update_user(request):
    """
    Ajax call to update a user's permissions
    """
    #TODO permission check
    pass