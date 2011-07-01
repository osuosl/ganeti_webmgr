# Copyright (C) 2010 Oregon State University et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from ganeti_web.models import VirtualMachine, VirtualMachineTemplate
from ganeti_web.forms.virtual_machine import VirtualMachineTemplateForm, \
    VirtualMachineTemplateCopyForm, NewVirtualMachineForm


@login_required
def templates(request):
    templates = VirtualMachineTemplate.objects.all()
    return render_to_response('ganeti/vm_template/list.html', {
        'templates':templates,
        },
        context_instance = RequestContext(request)
    )


@login_required
def create(request, template_id=None):
    """
    View to create or edit a new VirtualMachineTemplate.

    @param template_id Will populate the form with data from a template.
    """
    obj = None
    if template_id:
        obj = VirtualMachineTemplate.objects.get(pk=template_id)

    if request.method == "GET":
        form = VirtualMachineTemplateForm(instance=obj)
    elif request.method == "POST":
        form = VirtualMachineTemplateForm(request.POST, instance=obj)
        if form.is_valid():
            template = form.save()
            return HttpResponseRedirect(reverse('template-detail', 
                args=[template.id]))
    else:
        return HttpResponseNotAllowed(["GET","POST"])

    if obj:
        action = reverse('template-edit', args=[template_id])
    else:
        action = reverse('template-create')

    return render_to_response('ganeti/vm_template/create.html', {
        'form':form,
        'action':action,
        },
        context_instance = RequestContext(request)
    )


@login_required
def create_from_instance(request, instance):
    """
    View used to create a template from a virtual machine instance.
    """
    vm = get_object_or_404(VirtualMachine, hostname=instance)
    initial = instance_to_template(vm)

    if request.method == "GET":
        form = VirtualMachineTemplateForm(initial=initial, hypervisor='kvm')
    elif request.method == "POST":
        form = VirtualMachineTemplateForm(request.POST)
    else:
        return HttpResponseNotAllowed(["GET","POST"])

    return render_to_response('ganeti/vm_template/create.html', {
        'form': form,
        'action':reverse('template-create-from-instance', args=[instance]),
        },
        context_instance = RequestContext(request)
    )


def instance_to_template(instance):
    tmp = VirtualMachineTemplate()
    initial = dict(
        disk_size = instance.disk_size,
    )
    if isinstance(instance, VirtualMachine):
        for k, v in instance.info.items():
            if isinstance(v, dict):
                for i, j in v.items():
                    if hasattr(tmp, i):
                        initial[i] = j
            else:
                if hasattr(tmp, k):
                    initial[k] = v

    return initial


@login_required
def detail(request, template_id):
    vm_template = get_object_or_404(VirtualMachineTemplate, pk=template_id)
    return render_to_response('ganeti/vm_template/detail.html', {
        'template':vm_template,
        },
        context_instance = RequestContext(request)
    )


@login_required
def copy(request, template_id):
    """
    View used to create a copy of a VirtualMachineTemplate
    """
    obj = get_object_or_404(VirtualMachineTemplate, pk=template_id)
    if request.method == "GET":
        form = VirtualMachineTemplateCopyForm()
        return render_to_response('ganeti/vm_template/copy.html', {
            'form':form,
            'template':obj,
            },
            context_instance = RequestContext(request)
        )
    elif request.method == "POST":
        form = VirtualMachineTemplateCopyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            name = data.get('template_name', 'unnamed')
            desc = data.get('description', None)
            # Set pk to None to create new object instead of editing
            #  current one.
            obj.pk = None
            obj.template_name = name
            obj.description = desc
            obj.save()
        return HttpResponseRedirect(reverse('template-detail', 
                            args=[obj.id]))
    return HttpResponseNotAllowed(["GET", "POST"])


@login_required
def delete(request, template_id):
    if request.method == "DELETE":
        try:
            vm_template = VirtualMachineTemplate.objects.get(pk=template_id)
            vm_template.delete()
        except VirtualMachineTemplate.DoesNotExist:
            return HttpResponse('-1', mimetype='application/json')
        return HttpResponse('1', mimetype='application/json')
    return HttpResponseNotAllowed(["DELETE"])
