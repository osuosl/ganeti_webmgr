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
                
        
def vnc(request, cluster_slug, instance):
    if not check_instance_auth(request, cluster_slug, instance):
        return HttpResponseForbidden(content='You do not have sufficient privileges')

    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    port, password = cluster.setup_vnc_forwarding(instance)

    return render_to_response("vnc.html",
                              {'cluster': cluster,
                               'instance': instance,
                               'host': request.META['HTTP_HOST'],
                               'port': port,
                               'password': password,
                               'user': request.user})


def shutdown(request, cluster_slug, instance):
    if not check_instance_auth(request, cluster_slug, instance):
        return HttpResponseForbidden(content='You do not have sufficient privileges')

    vm = VirtualMachine.objects.get(hostname=instance)
    vm.shutdown()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def startup(request, cluster_slug, instance):
    if not check_instance_auth(request, cluster_slug, instance):
        return HttpResponseForbidden(content='You do not have sufficient privileges')
        
    vm = VirtualMachine.objects.get(hostname=instance)
    vm.startup()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def reboot(request, cluster_slug, instance):
    if not check_instance_auth(request, cluster_slug, instance):
        return HttpResponseForbidden(content='You do not have sufficient privileges')

    vm = VirtualMachine.objects.get(hostname=instance)
    vm.reboot()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def create(request, cluster_slug):
    hostname = get_object_or_404(Cluster, slug=cluster_slug)
    new_vm = VirtualMachine(cluster=hostname)
    oslist = new_vm.rapi.GetOperatingSystems()
    if request.POST:
        form = InstanceCreateForm(request.POST, instance=new_vm)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.META['HTTP_REFERER']) # Redirect after POST
    else:
        form = InstanceCreateForm(instance=new_vm)
        
    return render_to_response('instance_create.html', {
        'form': form,
        'oslist': oslist,
        'hostname': hostname,
    })

class InstanceCreateForm(forms.ModelForm):
    class Meta:
        model = VirtualMachine

class InstanceConfigForm(forms.Form):
    nic_type = forms.ChoiceField(label="Network adapter model",
                                 choices=(('paravirtual', 'Paravirtualized'),
                                          ('rtl8139', 'Realtek 8139+'),
                                          ('e1000', 'Intel PRO/1000'),
                                          ('ne2k_pci', 'NE2000 PCI')))

    disk_type = forms.ChoiceField(label="Hard disk type", 
                                  choices=(('paravirtual', 'Paravirtualized'),
                                           ('scsi', 'SCSI'),
                                           ('ide', 'IDE')))

    boot_order = forms.ChoiceField(label="Boot device",
                                   choices=(('disk', 'Hard disk'),
                                            ('cdrom', 'CDROM')))

    cdrom_type = forms.ChoiceField(label="CD-ROM Drive", 
                                   choices=(('none', 'Disabled'), 
                                            ('iso', 'ISO Image over HTTP (see below)')),
                                   widget=forms.widgets.RadioSelect())

    cdrom_image_path = forms.CharField(required=False, label="ISO Image URL (http)")
    use_localtime = forms.BooleanField(label="Hardware clock uses local time instead of UTC", required=False)

    def clean_cdrom_image_path(self):
        data = self.cleaned_data['cdrom_image_path']
        if data: 
            if not (data == 'none' or data.startswith('http://')):
                raise forms.ValidationError('Only HTTP URLs are allowed')
        
            elif data != 'none':
                # Check if the image is there
                oldtimeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(5)
                try:
                    print "Trying to open"
                    response = urllib2.urlopen(data)
                    socket.setdefaulttimeout(oldtimeout)
                except ValueError:
                    socket.setdefaulttimeout(oldtimeout)
                    raise forms.ValidationError('%s is not a valid URL' % data)
                except: # urllib2 HTTP errors
                    socket.setdefaulttimeout(oldtimeout)
                    raise forms.ValidationError('Invalid URL')
        return data


def instance(request, cluster_slug, instance):
    if not check_instance_auth(request, cluster_slug, instance):
        return HttpResponseForbidden(content="You do not have"
                                             " sufficient privileges")

    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    instance = VirtualMachine.objects.get(hostname=instance)
    if request.method == 'POST':
        configform = InstanceConfigForm(request.POST)
        if configform.is_valid():
            if configform.cleaned_data['cdrom_type'] == 'none':
                configform.cleaned_data['cdrom_image_path'] = 'none'
            elif configform.cleaned_data['cdrom_image_path'] != instance.hvparams['cdrom_image_path']:
                # This should be an http URL
                if not (configform.cleaned_data['cdrom_image_path'].startswith('http://') or 
                        configform.cleaned_data['cdrom_image_path'] == 'none'):
                    # Remove this, we don't want them to be able to read local files
                    del configform.cleaned_data['cdrom_image_path']
            instance.set_params(**configform.cleaned_data)
            sleep(1)
            return HttpResponseRedirect(request.path) 
            
    else: 
        if instance.info['hvparams']['cdrom_image_path']:
            instance.info['hvparams']['cdrom_type'] = 'iso'
        else:
            instance.info['hvparams']['cdrom_type'] = 'none'
        configform = InstanceConfigForm(instance.info['hvparams'])

    return render_to_response("instance.html",
                              {'cluster': cluster,
                               'instance': instance,
                               'configform': configform,
                               'user': request.user })


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