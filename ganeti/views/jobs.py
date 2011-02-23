import json
from django.template.context import RequestContext

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response

from ganeti.models import Job, Cluster, VirtualMachine, Node
from ganeti.views import render_403


@login_required
def status(request, cluster_slug, job_id):
    """
    returns the raw info of a job
    """
    job = get_object_or_404(Job, cluster__slug=cluster_slug, job_id=job_id)
    return HttpResponse(json.dumps(job.info), mimetype='application/json')


@login_required
def detail(request, cluster_slug, job_id):
    job = get_object_or_404(Job, cluster__slug=cluster_slug, job_id=job_id)

    user = request.user
    cluster_admin = True if user.is_superuser else user.has_perm('admin', job.cluster)

    return render_to_response("job/detail.html",{
        'job':job,
        'cluster_admin':cluster_admin
    } ,context_instance=RequestContext(request))


@login_required
def clear(request, cluster_slug, job_id):
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
            return render_403(request, "You do not have sufficient privileges")
        elif isinstance(obj, (VirtualMachine,)):
            # object is a virtual machine, check perms on VM and on Cluster
            if not (obj.owner_id == user.get_profile().pk  \
                or user.has_perm('admin', obj) \
                or user.has_perm('admin', obj.cluster)):
                    return render_403(request, "You do not have sufficient privileges")

    
    # clear the error.
    Job.objects.filter(pk=job.pk).update(cleared=True)

    # clear the job from the object, but only if it is the last job. It's
    # possible another job was started after this job, and the error message
    # just wasn't cleared.
    ObjectModel = job.obj.__class__
    ObjectModel.objects.filter(pk=job.object_id, last_job=job) \
        .update(last_job=None, ignore_cache=False)
    
    return HttpResponse('1', mimetype='application/json')