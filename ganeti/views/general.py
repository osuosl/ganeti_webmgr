import urllib2
import os
import socket

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from ganeti_webmgr.ganeti.models import *
from ganeti_webmgr.util.portforwarder import forward_port


@login_required
def index(request):
    clusterlist = Cluster.objects.all()
    return render_to_response("index.html", {
        'clusterlist': clusterlist,
        'user' : request.user,
            },
            context_instance=RequestContext(request),
        )


@login_required
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
        return HttpResponseRedirect(request.GET['next'])
    else:
        form = LoginForm()
    return render_to_response('login.html', {
        'form': form,
        },
        context_instance=RequestContext(request),
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
    vmcount = VirtualMachine.objects.count()
    
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
    
    return render_to_response("orphans.html", {
        'vms': vms,
        'vmcount': vmcount,
        'form':form,
        'user': request.user,
        },
        context_instance=RequestContext(request),
    )


class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, widget=forms.widgets.PasswordInput)


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