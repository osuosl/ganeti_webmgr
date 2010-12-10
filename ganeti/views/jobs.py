import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ganeti.models import Job


def status(request, cluster_slug, job_id):
    """
    returns the raw info of a job
    """
    job = get_object_or_404(Job, cluster__slug=cluster_slug, job_id=job_id)
    return HttpResponse(json.dumps(job.info), mimetype='application/json')