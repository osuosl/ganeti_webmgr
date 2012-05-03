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
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import simplejson as json
from django.views.generic.detail import DetailView

from ganeti_web.middleware import Http403
from ganeti_web.models import Job, Cluster, VirtualMachine, Node
from ganeti_web.views.generic import NO_PRIVS, LoginRequiredMixin

class JobDetailView(LoginRequiredMixin, DetailView):

    template_name = "ganeti/job/detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Job, job_id=self.kwargs["job_id"],
                                 cluster__slug=self.kwargs["cluster_slug"])

    def get_context_data(self, **kwargs):
        job = kwargs["object"]
        user = self.request.user
        admin = user.is_superuser or user.has_perm("admin", job.cluster)

        return {
            "job": job,
            "cluster_admin": admin,
        }

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
                raise Http403(NO_PRIVS)
        elif isinstance(obj, (VirtualMachine,)):
            # object is a virtual machine, check perms on VM and on Cluster
            if not (obj.owner_id == user.get_profile().pk  \
                or user.has_perm('admin', obj) \
                or user.has_perm('admin', obj.cluster)):
                    raise Http403(NO_PRIVS)


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
