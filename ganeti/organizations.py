from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response

from ganeti.models import Organization

def detail(request, id):
    """
    Display organization details
    """
    #TODO permission check
    
    org = get_object_or_404(Organization, id=id)
    return render_to_response("organization.html", {'org':org})


def add_user(request):
    """
    ajax call to add a user to an organization.
    """
    #TODO permission check
    
    pass



def remove_user(request):
    """
    Ajax call to remove a user from an organization
    """
    #TODO permission check
    
    pass


def update_user(request):
    """
    Ajax call to update a user's permissions
    """
    #TODO permission check
    
    pass