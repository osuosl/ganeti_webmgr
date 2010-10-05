from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from ganeti_webmgr.ganeti.models import *
from ganeti_webmgr.util.portforwarder import forward_port

@login_required
def vnc(request, cluster_slug, instance):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    port, password = cluster.setup_vnc_forwarding(instance)

    return render_to_response("vnc.html",
                              {'cluster': cluster,
                               'instance': instance,
                               'host': request.META['HTTP_HOST'],
                               'port': port,
                               'password': password,
                               'user': request.user},
        context_instance=RequestContext(request),
    )

@login_required
def shutdown(request, cluster_slug, instance):
    vm = VirtualMachine.objects.get(hostname=instance)
    vm.shutdown()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def startup(request, cluster_slug, instance):
    vm = VirtualMachine.objects.get(hostname=instance)
    vm.startup()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def reboot(request, cluster_slug, instance):
    vm = VirtualMachine.objects.get(hostname=instance)
    vm.reboot()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def create(request, cluster_slug=None):
    if cluster_slug is not None:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
    else:
        cluster = None

    if request.POST:
        form = NewVirtualMachineForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.META['HTTP_REFERER']) # Redirect after POST
    else:
        form = NewVirtualMachineForm(initial={'cluster':cluster})

    return render_to_response('instance_create.html', {
        'form': form,
        #'oslist': oslist,
        #'hostname': hostname,
        'user': request.user,
        },
        context_instance=RequestContext(request),
    )

@login_required
def list(request):
    vmlist = VirtualMachine.objects.all()
    return render_to_response('virtual_machine/list.html', {
        'vmlist' : vmlist
        },
        context_instance=RequestContext(request),
    )

@login_required
def detail(request, cluster_slug, instance):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    instance = get_object_or_404(VirtualMachine, hostname=instance)
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

    return render_to_response("virtual_machine/detail.html", {
        'cluster': cluster,
        'instance': instance,
        'configform': configform,
        'user': request.user,
        },
        context_instance=RequestContext(request),
    )

FQDN_RE = r'^[\w]+(\.[\w]+)*$'

def os_choices(cluster_slug):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    oslist = cluster.rapi.GetOperatingSystems()
    return list((os, os) for os in oslist)

def node_choices(cluster_slug):
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    nodelist = cluster.rapi.GetNodes()
    return list((node['id'], node['id']) for node in nodelist)

class NewVirtualMachineForm(forms.Form):
    cluster = forms.ModelChoiceField(queryset=Cluster.objects.all(), label='Cluster')
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), label='Owner')
    name = forms.RegexField(label='Instance Name', regex=FQDN_RE,
                            error_messages={
                                'invalid': 'Instance name must be resolvable',
                            })
    os   = forms.ChoiceField(label='Operating System', choices=[])
    mem  = forms.IntegerField(label='Memory (MB)', min_value=100)
    disk = forms.IntegerField(label='Disk Space (MB)', min_value=100)
    """
    def __init__(self, cluster_hostname=None, *args, **kwargs):
        super(NewVirtualMachineForm, self).__init__(*args, **kwargs)
        
        if cluster_slug is None:
            # Populate the Node lists
            nodes = node_choices(cluster_slug)
            self.fields['pnode'].choices = nodes
            self.fields['snode'].choices = nodes
            # Populate the OS List
            oss = os_choices(cluster_slug)
            self.fields['os'].choices = oss
            # Set cluster field
            self.fields['cluster'] = cluster_slug
        else:
            clusterlist = Cluster.objects.all()
            self.fields['cluster'] = clusterlist
    
    #pnode = forms.ChoiceField(label='Primary Node', choices=[])
    #snode = forms.ChoiceField(label='Secondary Node', choices=[])

    #def clean_snode(self):
    #    if self.cleaned_data['snode'] == self.cleaned_data['pnode']:
    #        raise forms.ValidationError("Secondary Node must not match"
    #                                    + " Primary")
    """

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