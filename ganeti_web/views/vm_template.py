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
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods, require_GET

from ganeti_web.models import Cluster, VirtualMachineTemplate, VirtualMachine
from ganeti_web.forms.vm_template import (VirtualMachineTemplateForm,
                                          VirtualMachineTemplateCopyForm)
from ganeti_web.forms.virtual_machine import NewVirtualMachineForm
from ganeti_web.views import render_403


@login_required
def templates(request):
    templates = VirtualMachineTemplate.objects.exclude(template_name=None)
    # Because templates do not have 'disk_size' this value
    #  is computed here to be easily displayed.
    for template in templates:
        template.disk_size = sum([disk['size'] for disk in template.disks])
    return render_to_response('ganeti/vm_template/list.html', {
        'templates':templates,
        },
        context_instance = RequestContext(request)
    )

@require_http_methods(["GET", "POST"])
@login_required
def edit(request, cluster_slug=None, template=None):
    """
    View to edit a new VirtualMachineTemplate.
    """
    user = request.user
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        if not (
            user.is_superuser or
            user.has_perm('admin', cluster) or
            user.has_perm('create_vm', cluster)
            ):
            return render_403(request, _("You do not have sufficient privileges"))

    if cluster_slug and template:
        obj = get_object_or_404(VirtualMachineTemplate, template_name=template,
                                cluster__slug=cluster_slug)

    if request.method == "GET":
        initial = vars(obj)
        initial['cluster'] = cluster.id
        form = VirtualMachineTemplateForm(user=user, initial=initial)
    elif request.method == "POST":
        form = VirtualMachineTemplateForm(request.POST, user=user)
        if form.is_valid():
            form.instance.pk = obj.pk
            form_obj = form.save()
            return HttpResponseRedirect(reverse('template-detail',
                args=[form_obj.cluster.slug, form_obj]))

    return render_to_response('ganeti/vm_template/create.html', {
        'form':form,
        'action':reverse('template-edit', args=[cluster_slug, obj]),
        'template':obj,
        },
        context_instance = RequestContext(request)
    )

@require_http_methods(["GET", "POST"])
@login_required
def create(request):
    """
    View to create a new VirtualMachineTemplate.

    @param template Will populate the form with data from a template.
    """
    user = request.user
    if request.method == "GET":
        form = VirtualMachineTemplateForm(user=user)
    elif request.method == "POST":
        form = VirtualMachineTemplateForm(request.POST, user=user)
        if form.is_valid():
            form_obj = form.save()
            return HttpResponseRedirect(reverse('template-detail',
                args=[form_obj.cluster.slug, form_obj]))

    return render_to_response('ganeti/vm_template/create.html', {
        'form':form,
        'action':reverse('template-create'),
        },
        context_instance = RequestContext(request)
    )


@require_GET
@login_required
def create_template_from_instance(request, cluster_slug, instance):
    """
    View to create a new template from a given instance.
      Post method is handled by template create view.
    """
    user = request.user
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        if not (
            user.is_superuser or
            user.has_perm('admin', cluster) or
            user.has_perm('create_vm', cluster)
            ):
            return render_403(request, _("You do not have sufficient privileges"))

    vm = get_object_or_404(VirtualMachine, hostname=instance,
        cluster__slug=cluster_slug)

    # Work with vm vars here
    info = vm.info
    links = info['nic.links']
    modes = info['nic.modes']
    sizes = info['disk.sizes']

    initial = dict(
        template_name=instance,
        cluster=cluster.id,
        start=info['admin_state'],
        disk_template=info['disk_template'],
        disk_type=info['hvparams']['disk_type'],
        nic_type=info['hvparams']['nic_type'],
        os=vm.operating_system,
        vcpus=vm.virtual_cpus,
        memory=vm.ram,
        disks=[{'size':size} for size in sizes],
        nics=[{'mode':mode, 'link':link} for mode, link in zip(modes, links)],
        nic_count=len(links),
    )
    form = VirtualMachineTemplateForm(user=user, initial=initial)

    return render_to_response('ganeti/vm_template/create.html', {
        'form':form,
        'from_vm':vm,
        'action':reverse('template-create'),
        },
        context_instance = RequestContext(request)
    )


@require_GET
@login_required
def create_instance_from_template(request, cluster_slug, template):
    """
    View to create a new instance from a given template.
      Post method is handled by virtual_machine create view.
    """
    user = request.user
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        if not (
            user.is_superuser or
            user.has_perm('admin', cluster) or
            user.has_perm('create_vm', cluster)
            ):
            return render_403(request, _("You do not have sufficient privileges"))

    vm_template = get_object_or_404(VirtualMachineTemplate,
                                    template_name=template,
                                    cluster__slug=cluster_slug)

    # Work with vm_template vars here
    initial = dict(
        hostname=vm_template.template_name,
        cluster=vm_template.cluster_id,
    )
    initial.update(vars(vm_template))
    ignore_fields = ('disks', '_state', 'pnode', 'snode',
        'description')
    for field in ignore_fields:
        del initial[field]
    initial['disk_count'] = len(vm_template.disks)
    for i,disk in enumerate(vm_template.disks):
        initial['disk_size_%s'%i] = disk['size']
    form = NewVirtualMachineForm(user, initial=initial)
    cluster_defaults = {} #cluster_default_info(cluster)

    return render_to_response('ganeti/virtual_machine/create.html', {
        'form':form,
        'cluster_defaults':json.dumps(cluster_defaults),
        },
        context_instance = RequestContext(request)
    )


@login_required
def detail(request, cluster_slug, template):
    user = request.user
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        if not (
            user.is_superuser or
            user.has_perm('admin', cluster) or
            user.has_perm('create_vm', cluster)
            ):
            return render_403(request, _("You do not have sufficient privileges"))

    vm_template = get_object_or_404(VirtualMachineTemplate,
                                    template_name=template,
                                    cluster__slug=cluster_slug)
    return render_to_response('ganeti/vm_template/detail.html', {
        'template':vm_template,
        'cluster':cluster_slug,
        },
        context_instance = RequestContext(request)
    )


@require_http_methods(["GET", "POST"])
@login_required
def copy(request, cluster_slug, template):
    """
    View used to create a copy of a VirtualMachineTemplate
    """
    user = request.user
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        if not (
            user.is_superuser or
            user.has_perm('admin', cluster) or
            user.has_perm('create_vm', cluster)
            ):
            return render_403(request, _("You do not have sufficient privileges"))

    obj = get_object_or_404(VirtualMachineTemplate, template_name=template,
                                    cluster__slug=cluster_slug)
    if request.method == "GET":
        form = VirtualMachineTemplateCopyForm()
        return render_to_response('ganeti/vm_template/copy.html', {
            'form':form,
            'template':obj,
            'cluster':cluster_slug,
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
                            args=[cluster_slug, obj]))


@login_required
@require_http_methods(["DELETE"])
def delete(request, cluster_slug, template):
    user = request.user
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
        if not (
            user.is_superuser or
            user.has_perm('admin', cluster) or
            user.has_perm('create_vm', cluster)
            ):
            return render_403(request, _("You do not have sufficient privileges"))

    try:
        vm_template = VirtualMachineTemplate.objects.get(template_name=template,
                                                         cluster__slug=cluster_slug)
        vm_template.delete()
    except VirtualMachineTemplate.DoesNotExist:
        return HttpResponse('-1', mimetype='application/json')
    return HttpResponse('1', mimetype='application/json')
