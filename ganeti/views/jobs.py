import json
from django.template.context import RequestContext

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response

from ganeti.models import Job, Cluster, VirtualMachine
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
def clear(request):
    """
    Clear a single failed job error message
    """
    user = request.user
    job = get_object_or_404(Job, pk=request.POST.get('id', None))
    obj = job.obj
    
    # if not a superuser, check permissions on the object itself
    if not user.is_superuser:
        if isinstance(obj, (Cluster,)) and not user.has_perm('admin', obj):
            return render_403(request, "You do not have sufficient privileges")
        elif isinstance(obj, (VirtualMachine,)):
            # object is a virtual machine, check perms on VM and on Cluster
            if not (obj.owner_id == user.get_profile().pk  \
                or user.has_perm('admin', obj) \
                or user.has_perm('admin', obj.cluster)):
                    return render_403(request, "You do not have sufficient privileges")
    
    # clear the error
    Job.objects.filter(pk=job.pk).update(cleared=True)
    
    return HttpResponse('1', mimetype='application/json')