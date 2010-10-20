from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext

from ganeti.models import VirtualMachine, Cluster, ClusterUser


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


@login_required
def orphans(request):
    """
    displays list of orphaned VirtualMachines, i.e. VirtualMachines without
    an owner.
    """
    user = request.user
    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.filter_on_perms(Cluster, ['admin'])
        if not clusters:
            return HttpResponseForbidden()
    
    vms = VirtualMachine.objects.filter(owner=None, cluster__in=clusters) \
                                            .values_list('id','hostname')
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
    
    return render_to_response("importing/orphans.html", {
        'vms': vms,
        'vmcount': vmcount,
        'form':form,
        'user': request.user,
        },
        context_instance=RequestContext(request),
    )


@login_required
def missing_ganeti(request):
    """
    View for displaying VirtualMachines missing from the ganeti cluster
    """
    pass


@login_required
def missing_db(request):
    """
    View for displaying VirtualMachines missing from the database
    """
    pass


