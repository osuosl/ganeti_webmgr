import json
import os
import socket
import urllib2

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from object_permissions import get_model_perms, get_user_perms, grant, revoke, \
    get_users, get_groups, get_group_perms
from object_permissions.views.permissions import view_users, view_permissions
from ganeti.models import *
from util.portforwarder import forward_port

# Regex for a resolvable hostname
FQDN_RE = r'^[\w]+(\.[\w]+)*$'


@login_required
def detail(request, cluster_slug):
    """
    Display details of a cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    admin = True if user.is_superuser else user.has_perm('admin', cluster)
    if not admin:
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    return render_to_response("cluster/detail.html", {
        'cluster': cluster,
        'user': request.user,
        'admin' : admin
        },
        context_instance=RequestContext(request),
    )


@login_required
def nodes(request, cluster_slug):
    """
    Display all nodes in a cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    return render_to_response("node/table.html", \
                        {'cluster': cluster, 'nodes':cluster.nodes(True)}, \
        context_instance=RequestContext(request),
    )


@login_required
def virtual_machines(request, cluster_slug):
    """
    Display all virtual machines in a cluster.  Filtered by access the user
    has permissions for
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    admin = True if user.is_superuser else user.has_perm('admin', cluster)
    if not admin:
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    if admin:
        vms = cluster.virtual_machines.all()
    else:
        vms = user.filter_on_perms(['admin'], VirtualMachine, cluster=cluster)
    
    return render_to_response("virtual_machine/table.html", \
                {'cluster': cluster, 'vms':vms}, \
                context_instance=RequestContext(request))


@login_required
def edit(request, cluster_slug=None):
    """
    Edit a cluster
    """
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
    else:
        cluster = None
    
    user = request.user
    if not (user.is_superuser or (cluster and user.has_perm('admin', cluster))):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = EditClusterForm(request.POST, instance=cluster)
        if form.is_valid():
            cluster = form.save()
            cluster.sync_virtual_machines()
            return HttpResponseRedirect(reverse('cluster-detail', \
                                                args=[cluster.slug]))
    
    elif request.method == 'DELETE':
        cluster.delete()
        return HttpResponse('1', mimetype='application/json')
    
    else:
        form = EditClusterForm(instance=cluster)
    
    return render_to_response("cluster/edit.html", {
        'form' : form,
        'cluster': cluster,
        },
        context_instance=RequestContext(request),
    )


@login_required
def list_(request):
    """
    List all clusters
    """
    user = request.user
    if user.is_superuser:
        cluster_list = Cluster.objects.all()
    else:
        cluster_list = user.filter_on_perms(Cluster, ['admin', 'create_vm'])
    return render_to_response("cluster/list.html", {
        'cluster_list': cluster_list,
        'user': request.user,
        },
        context_instance=RequestContext(request),
    )


@login_required
def users(request, cluster_slug):
    """
    Display all of the Users of a Cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    url = reverse('cluster-permissions', args=[cluster.slug])
    return view_users(request, cluster, url, template='cluster/users.html')


@login_required
def permissions(request, cluster_slug, user_id=None, group_id=None):
    """
    Update a users permissions.
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")

    url = reverse('cluster-permissions', args=[cluster.slug])
    return view_permissions(request, cluster, url, user_id, group_id,
                            user_template='cluster/user_row.html',
                            group_template='cluster/group_row.html')


class QuotaForm(forms.Form):
    """
    Form for editing user quota on a cluster
    """
    input = forms.TextInput(attrs={'size':5})
    
    user = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), \
                                  widget=forms.HiddenInput)
    ram = forms.IntegerField(label='Memory (MB)', required=False, min_value=0, \
                             widget=input)
    virtual_cpus = forms.IntegerField(label='Virtual CPUs', required=False, \
                                    min_value=0, widget=input)
    disk = forms.IntegerField(label='Disk Space (MB)', required=False, \
                              min_value=0, widget=input)
    delete = forms.BooleanField(required=False, widget=forms.HiddenInput)


@login_required
def quota(request, cluster_slug, user_id):
    """
    Updates quota for a user
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        return HttpResponseForbidden("You do not have sufficient privileges")
    
    if request.method == 'POST':
        form = QuotaForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cluster_user = data['user']
            if data['delete']:
                cluster.set_quota(cluster_user)
            else:
                quota = cluster.get_quota()
                same = data['virtual_cpus'] == quota['virtual_cpus'] \
                    and data['disk']==quota['disk'] \
                    and data['ram']==quota['ram']
                if same:
                    # same as default, set quota to default.
                    cluster.set_quota(cluster_user)
                else:
                    cluster.set_quota(cluster_user, data)
            
            # return updated html
            cluster_user = cluster_user.cast()
            url = reverse('cluster-permissions', args=[cluster.slug])
            if isinstance(cluster_user, (Profile,)):
                return render_to_response("cluster/user_row.html",
                    {'object':cluster, 'user':cluster_user.user, 'url':url})
            else:
                return render_to_response("cluster/group_row.html",
                    {'object':cluster, 'group':cluster_user.user_group, \
                     'url':url})
        
        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')
    
    if user_id:
        cluster_user = get_object_or_404(ClusterUser, id=user_id)
        quota = cluster.get_quota(cluster_user)
        data = {'user':user_id}
        if quota:
            data.update(quota)
    else:
        return HttpResponseNotFound('User was not found')
    
    form = QuotaForm(data)
    return render_to_response("cluster/quota.html", \
                        {'form':form, 'cluster':cluster, 'user_id':user_id}, \
                        context_instance=RequestContext(request))


class EditClusterForm(forms.ModelForm):
    class Meta:
        model = Cluster