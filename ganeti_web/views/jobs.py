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

import json
from django.template.context import RequestContext

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response

from ganeti_web.models import Job, Cluster, VirtualMachine, Node
from ganeti_web.views import render_403
from django.utils.translation import ugettext as _

@login_required
def status(request, cluster_slug, job_id, rest=False):
    """
    returns the raw info of a job
    """
    job = get_object_or_404(Job, cluster__slug=cluster_slug, job_id=job_id)
    if rest:
        return job
    else:
        return HttpResponse(json.dumps(job.info), mimetype='application/json')


@login_required
def detail(request, cluster_slug, job_id, rest=False):
    job = get_object_or_404(Job, cluster__slug=cluster_slug, job_id=job_id)

    user = request.user
    cluster_admin = True if user.is_superuser else user.has_perm('admin', job.cluster)

    if rest:
        return {'job': job, 'cluster_admin':cluster_admin}
    else:
        return render_to_response("ganeti/job/detail.html",{
            'job':job,
            'cluster_admin':cluster_admin
        } ,context_instance=RequestContext(request))


@login_required
def clear(request, cluster_slug, job_id, rest=False):
    """
    Clear a single failed job error message
    """
    
    user = request.user
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    job = get_object_or_404(Job, cluster__slug=cluster_slug, job_id=job_id)
    obj = job.obj

    # if not a superuser, check permissions on the object itself
    cluster_admin = user.is_superuser or user.has_perm('admin', cluster)

    if not cluster_admin:
        if isinstance(obj, (Cluster, Node)):
            if rest:
                return HttpResponseForbidden
            else:
                return render_403(request, _("You do not have sufficient privileges"))
        elif isinstance(obj, (VirtualMachine,)):
            # object is a virtual machine, check perms on VM and on Cluster
            if not (obj.owner_id == user.get_profile().pk  \
                or user.has_perm('admin', obj) \
                or user.has_perm('admin', obj.cluster)):
                    if rest:
                        return HttpResponseForbidden
                    else:
                        return render_403(request, _("You do not have sufficient privileges"))

    
    # clear the error.
    Job.objects.filter(pk=job.pk).update(cleared=True)

    # clear the job from the object, but only if it is the last job. It's
    # possible another job was started after this job, and the error message
    # just wasn't cleared.
    #
    # XXX object could be none, in which case we dont need to clear its last_job
    if obj is not None:
        ObjectModel = obj.__class__
        ObjectModel.objects.filter(pk=job.object_id, last_job=job)  \
            .update(last_job=None, ignore_cache=False)

    if rest:
        return 1
    else:
        return HttpResponse('1', mimetype='application/json')
