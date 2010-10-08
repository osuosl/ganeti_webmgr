from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from ganeti_webmgr.ganeti.models import *
from ganeti_webmgr.util.portforwarder import forward_port
from ganeti_webmgr.util.client import GanetiApiError

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
    """
    Create a new instance
        Store in DB and
        Create on given cluster
    """
    if cluster_slug is not None:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        oslist = os_choices(cluster_slug)
    else:
        cluster = None
        oslist = None

    if request.method == 'POST':
        form = NewVirtualMachineForm(request.POST, oslist=oslist)
        if form.is_valid():
            cluster = form.cleaned_data['cluster']
            hostname = form.cleaned_data['hostname']
            owner = form.cleaned_data['owner']
            #virtual_cpus = form.cleaned_data['vcpus']
            disk_size = form.cleaned_data['disk_size']
            ram = form.cleaned_data['ram']
            disk_template = form.cleaned_data['disk_template']
            os = form.cleaned_data['os']
            vm = VirtualMachine(cluster=cluster, owner=owner, hostname=hostname, \
                                disk_size=disk_size, ram=ram, virtual_cpus=2, \
                                node='gtest1.osuosl.bak')
            vm.save()
            c = get_object_or_404(Cluster, hostname=cluster)
            jobid = 0
            try:
                jobid = c.rapi.CreateInstance('create', hostname, disk_template, \
                                  [{"size": disk_size, }],[{"link": "br42", }], \
                                  memory=ram, os=os, vcpus=2, \
                                  pnode='gtest1.osuosl.bak') #\
                                  #hvparams={}, beparams={})
            except GanetiApiError as e:
                print jobid
                print e
            #print jobid
            return HttpResponseRedirect(request.META['HTTP_REFERER']) # Redirect after POST
    else:
        form = NewVirtualMachineForm(initial={'cluster':cluster,},oslist=oslist)

    return render_to_response('virtual_machine/create.html', {
        'form': form,
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
    oslister = cluster.rapi.GetOperatingSystems()
    oslist = []
    for os in oslister:
        oslist.append((os,os))
    return oslist #list((os, os) for os in oslist) #[('stuff', 'stuff')]

def node_choices(cluster_slug):
    cluster = get_object_or_404(Cluster, hostname=cluster_slug)
    nodelist = cluster.rapi.GetNodes()
    return list((node['id'], node['id']) for node in nodelist)

class NewVirtualMachineForm(forms.Form):
    cluster = forms.ModelChoiceField(queryset=Cluster.objects.all(), label='Cluster')
    owner = forms.ModelChoiceField(queryset=ClusterUser.objects.all(), label='Owner')
    hostname = forms.RegexField(label='Instance Name', regex=FQDN_RE,
                            error_messages={
                                'invalid': 'Instance name must be resolvable',
                            })
    disk_template = forms.ChoiceField(label='Disk Template', choices=[('plain', 'plain'),('drdb', 'drdb'),\
            ('file','file'), ('diskless', 'diskless')])
    os   = forms.ChoiceField(label='Operating System', choices=[])
    ram  = forms.IntegerField(label='Memory (MB)', min_value=100)
    disk_size = forms.IntegerField(label='Disk Space (MB)', min_value=100)
    
    def __init__(self, *args, **kwargs):
        oslist = kwargs.pop('oslist', None)
        super(NewVirtualMachineForm, self).__init__(*args, **kwargs)
        
        #if hostname is not None:
            # Populate the Node lists
            #nodes = node_choices(cluster_slug)
            #self.fields['pnode'].choices = nodes
            #self.fields['snode'].choices = nodes
        if oslist is not None:
            # Populate the OS List
            self.fields['os'].choices = oslist
        else:
            #clusters = list(Cluster.objects.all()[:1])
            #cluster_slug = clusters[0].slug
            #oss = os_choices(cluster_slug)
            #self.fields['os'].choices = oss
            pass
        
    """
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