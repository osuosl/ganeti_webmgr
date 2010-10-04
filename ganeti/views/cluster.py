import urllib2
import os
import socket

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions import get_model_perms, get_user_perms, grant, revoke, \
    get_users
from object_permissions.views.permissions import ObjectPermissionForm
from ganeti.models import *
from util.portforwarder import forward_port


@login_required
def detail(request, cluster_slug):
    """
    Display details of a cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    vmlist = VirtualMachine.objects.filter(cluster__exact=cluster)
    return render_to_response("cluster.html", {
        'cluster': cluster,
        'user': request.user,
        'vmlist' : vmlist,
        },
        context_instance=RequestContext(request),
    )


def cluster_users(request, cluster_slug):
    """
    Display all of the users of a cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    users = get_users(cluster)
    
    return render_to_response("cluster/users.html",
                              {'cluster': cluster, 'users':users},
        context_instance=RequestContext(request),
    )


@login_required
def list(request):
    """
    List all clusters
    """
    cluster_list = Cluster.objects.all()
    return render_to_response("cluster_list.html", {
        'cluster_list': cluster_list,
        'user': request.user,
        },
        context_instance=RequestContext(request),
    )


def permissions(request, cluster_slug):
    """
    Update a users permissions.
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    if request.method == 'POST':
        form = ObjectPermissionForm(cluster, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            if form.update_perms():
                # return html to replace existing user row
                return render_to_response("cluster/user_row.html",
                                          {'cluster':cluster, 'user':user})
            else:
                # no permissions, send ajax response to remove user
                return HttpResponse('0', mimetype='application/json')
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    user_id = request.GET.get('user', None)
    if user_id:
        form_user = get_object_or_404(User, id=user_id)
        data = {'permissions':get_user_perms(form_user, cluster), \
                'user':user_id}
    else:
        data = {'permissions':[]}
    form = ObjectPermissionForm(cluster, data)
    return render_to_response("cluster/permissions.html", \
                        {'form':form, 'cluster':cluster, 'user_id':user_id}, \
                        context_instance=RequestContext(request))