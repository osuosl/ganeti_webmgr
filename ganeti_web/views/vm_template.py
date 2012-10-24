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
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView

from ganeti_web.backend.templates import (instance_to_template,
                                          template_to_instance)
from ganeti_web.forms.vm_template import (VirtualMachineTemplateCopyForm,
                                          VMInstanceFromTemplate,
                                          TemplateFromVMInstance)
from ganeti_web.middleware import Http403
from ganeti_web.models import Cluster, VirtualMachineTemplate, VirtualMachine
from ganeti_web.views.generic import NO_PRIVS, LoginRequiredMixin


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



class TemplateFromVMInstanceView(LoginRequiredMixin, FormView):
    """
    Create a template from a virtual machine instance.
    """

    form_class = TemplateFromVMInstance
    template_name = "ganeti/vm_template/to_instance.html"

    def _get_stuff(self):
        cluster_slug = self.kwargs["cluster_slug"]
        hostname = self.kwargs["instance"]

        self.cluster = get_object_or_404(Cluster, slug=cluster_slug)
        self.vm = get_object_or_404(VirtualMachine, hostname=hostname,
                                    cluster__slug=cluster_slug)

        user = self.request.user
        if not (
            user.is_superuser or
            user.has_perm('admin', self.cluster) or
            user.has_perm('create_vm', self.cluster)
            ):
            raise Http403(NO_PRIVS)


    def form_valid(self, form):
        """
        Create the new VM and then redirect to the new VM's page.
        """

        template_name = form.cleaned_data["template_name"]

        self._get_stuff()

        template = instance_to_template(self.vm, template_name)

        return HttpResponseRedirect(reverse("template-detail",
                                            args=[self.cluster.slug,
                                                  template.template_name]))


    def get_context_data(self, **kwargs):
        context = super(TemplateFromVMInstanceView,
                        self).get_context_data(**kwargs)

        self._get_stuff()

        context["vm"] = self.vm

        return context



class VMInstanceFromTemplateView(LoginRequiredMixin, FormView):
    """
    Create a virtual machine instance from a template.
    """

    form_class = VMInstanceFromTemplate
    template_name = "ganeti/vm_template/to_vm.html"

    def _get_stuff(self):
        cluster_slug = self.kwargs["cluster_slug"]
        template_name = self.kwargs["template"]

        self.cluster = get_object_or_404(Cluster, slug=cluster_slug)
        self.template = get_object_or_404(VirtualMachineTemplate,
                                          template_name=template_name,
                                          cluster__slug=cluster_slug)

        user = self.request.user
        if not (
            user.is_superuser or
            user.has_perm('admin', self.cluster) or
            user.has_perm('create_vm', self.cluster)
            ):
            raise Http403(NO_PRIVS)


    def form_valid(self, form):
        """
        Create the new VM and then redirect to the new VM's page.
        """

        hostname = form.cleaned_data["hostname"]
        owner = form.cleaned_data["owner"]

        self._get_stuff()

        vm = template_to_instance(self.template, hostname, owner)

        return HttpResponseRedirect(reverse('instance-detail',
                                            args=[self.cluster.slug,
                                                  vm.hostname]))


    def get_context_data(self, **kwargs):
        context = super(VMInstanceFromTemplateView,
                        self).get_context_data(**kwargs)

        self._get_stuff()

        context["template"] = self.template

        return context


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
            raise Http403(NO_PRIVS)

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
            raise Http403(NO_PRIVS)

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
            raise Http403(NO_PRIVS)

    try:
        vm_template = VirtualMachineTemplate.objects.get(template_name=template,
                                                         cluster__slug=cluster_slug)
        vm_template.delete()
    except VirtualMachineTemplate.DoesNotExist:
        return HttpResponse('-1', mimetype='application/json')
    return HttpResponse('1', mimetype='application/json')
