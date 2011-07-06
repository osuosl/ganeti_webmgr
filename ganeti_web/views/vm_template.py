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
from django.utils.translation import ugettext as _

from ganeti_web.models import Cluster, VirtualMachineTemplate
from ganeti_web.forms.virtual_machine import VirtualMachineTemplateForm, \
    VirtualMachineTemplateCopyForm
from ganeti_web.views import render_403


@login_required
def templates(request):
    templates = VirtualMachineTemplate.objects.all()
    return render_to_response('ganeti/vm_template/list.html', {
        'templates':templates,
        },
        context_instance = RequestContext(request)
    )


@login_required
def create(request, cluster_slug=None, template=None):
    """
    View to create or edit a new VirtualMachineTemplate.

    @param template Will populate the form with data from a template.
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

    obj = None
    if cluster_slug and template:
        obj = get_object_or_404(VirtualMachineTemplate, template_name=template,
                                cluster__slug=cluster_slug)

    if request.method == "GET":
        form = VirtualMachineTemplateForm(instance=obj, user=user)
    elif request.method == "POST":
        form = VirtualMachineTemplateForm(request.POST, user=user, 
                                          instance=obj)
        if form.is_valid():
            form_obj = form.save()
            return HttpResponseRedirect(reverse('template-detail', 
                args=[form_obj.cluster.slug, form_obj]))
    else:
        return HttpResponseNotAllowed(["GET","POST"])

    if obj:
        action = reverse('template-edit', args=[obj.cluster.slug, obj])
    else:
        action = reverse('template-create')

    return render_to_response('ganeti/vm_template/create.html', {
        'form':form,
        'action':action,
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
    return HttpResponseNotAllowed(["GET", "POST"])


@login_required
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

    if request.method == "DELETE":
        try:
            vm_template = VirtualMachineTemplate.objects.get(template_name=template,
                                                             cluster__slug=cluster_slug)
            vm_template.delete()
        except VirtualMachineTemplate.DoesNotExist:
            return HttpResponse('-1', mimetype='application/json')
        return HttpResponse('1', mimetype='application/json')
    return HttpResponseNotAllowed(["DELETE"])
