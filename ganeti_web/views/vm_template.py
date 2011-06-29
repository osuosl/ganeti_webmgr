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

from ganeti_web.models import VirtualMachineTemplate
from ganeti_web.forms.virtual_machine import VirtualMachineTemplateForm


@login_required
def templates(request):
    templates = VirtualMachineTemplate.objects.all()
    return render_to_response('ganeti/vm_template/list.html', {
        'templates':templates,
        },
        context_instance = RequestContext(request)
    )


@login_required
def create(request): 
    if request.method == "GET":
        form = VirtualMachineTemplateForm()
    elif request.method == "POST":
        form = VirtualMachineTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()
            return HttpResponseRedirect(reverse('template-detail', 
                args=[template.id]))
    else:
        return HttpResponseNotAllowed(["GET","POST"])

    return render_to_response('ganeti/vm_template/create.html', {
        'form':form
        },
        context_instance = RequestContext(request)
    )


@login_required
def detail(request, template_id):
    vm_template = get_object_or_404(VirtualMachineTemplate, pk=template_id)
    return render_to_response('ganeti/vm_template/detail.html', {
        'template':vm_template,
        },
        context_instance = RequestContext(request)
    )

