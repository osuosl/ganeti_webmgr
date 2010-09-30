import urllib2
import os
import socket


from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response


from models import *
from ganeti_webmgr.util.portforwarder import forward_port


def index(request):
    clusterlist = Cluster.objects.all()
    return render_to_response("index.html", {
        'clusterlist': clusterlist,
        'user' : request.user,
        })

def cluster_detail(request, cluster_slug):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    return render_to_response("cluster.html", {
        'cluster': cluster
    })

def check_instance_auth(request, cluster, instance):
    cluster = get_object_or_404(Cluster, slug=cluster)
    instance = cluster.instance(instance)
    if request.user.is_superuser or request.user in instance.users or \
            set.intersection(set(request.user.groups.all()), set(instance.groups)):
        return True
    return False


class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, widget=forms.widgets.PasswordInput)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                else:
                    return HttpResponseForbidden(content='Your account is disabled')
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

class OrphanForm(forms.Form):
    """
    Form used for assigning owners to VirtualMachines that do not yet have an
    owner (orphans).
    """
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all())
    virtual_machines = forms.MultipleChoiceField()

    def __init__(self, choices, *args, **kwargs):
        super(OrphanForm, self).__init__(*args, **kwargs)
        self.fields['virtual_machines'].choices = choices


def cluster_list(request):        
    cluster_list = Cluster.objects.all()
    return render_to_response("cluster_list.html", {'cluster_list': cluster_list })


@user_passes_test(lambda u: u.is_superuser)
def orphans(request):
    """
    displays list of orphaned VirtualMachines, i.e. VirtualMachines without
    an owner.
    """
    # synchronize all cluster objects
    for cluster in Cluster.objects.all():
        cluster.sync_virtual_machines()
        
    vms = VirtualMachine.objects.filter(owner=None).values_list('id','hostname')
    vms = list(vms)
    
    if request.method == 'POST':
        # process updates if this was a form submission
        form = OrphanForm(vms, request.POST)
        if form.is_valid():
            # update all selected VirtualMachines
            data = form.cleaned_data
            owner = data['owner']
            vm_ids = data['virtual_machines']
            VirtualMachine.objects.filter(id__in=vm_ids).update(owner=owner)
            
            # remove updated vms from the list
            vms = filter(lambda x: unicode(x[0]) not in vm_ids, vms)
        
    else:
        form = OrphanForm(vms)
    
    return render_to_response("orphans.html", {'vms': vms, 'form':form})