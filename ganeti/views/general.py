# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
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
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.contenttypes.models import ContentType

from ganeti.models import Cluster, VirtualMachine, Job, GanetiError
from ganeti.views import render_403


@login_required
def index(request):
    user = request.user

    # should be more complex query in future
    # like: user.is_admin_on_any(Cluster)
    if (user.is_superuser or user.has_any_perms(Cluster, ["admin",])):
        return HttpResponseRedirect(reverse("cluster-overview"))
    else:
        return HttpResponseRedirect(reverse("virtualmachine-list"))


def merge_errors(errors, jobs):
    """ helper function for merging queryset of GanetiErrors and Job Errors """
    merged = []
    job_iter = iter(jobs)
    try:
        job = job_iter.next()
    except StopIteration:
        job = None
    for error in errors:
        if job is None or error.timestamp > job.finished:
            merged.append((True, error))
        else:
            # found a newer job, append jobs till the next job is older
            while job is not None and job.finished > error.timestamp:
                merged.append((False, job))
                try:
                    job = job_iter.next()
                except StopIteration:
                    job = None
                    
    # append any left over jobs
    while job is not None:
        merged.append((False, job))
        try:
            job = job_iter.next()
        except StopIteration:
            job = None
    return merged


@login_required
def overview(request):
    """
    Status page
    """
    user = request.user

    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_all_perms(Cluster, ['admin',])
    admin = user.is_superuser or clusters

    #orphaned, ready to import, missing
    orphaned = import_ready = missing = 0

    # Get query containing any virtual machines the user has permissions for
    vms = user.get_objects_any_perms(VirtualMachine, groups=True).values('pk')

    if admin:
        # filter VMs from the vm list where the user is an admin.  These VMs are
        # already shown in that section
        vms = vms.exclude(cluster__in=clusters)
        
        # build list of admin tasks for this user's clusters
        orphaned = VirtualMachine.objects.filter(owner=None,
                cluster__in=clusters).count()
        for cluster in clusters:
            import_ready += len(cluster.missing_in_db)
            missing += len(cluster.missing_in_ganeti)
    
    # build list of job errors.  Include jobs from any vm the user has access to
    # If the user has admin on any cluster then those clusters and it's objects
    # must be included too.
    #
    # XXX all jobs have the cluster listed, filtering by cluster includes jobs
    # for both the cluster itself and any of its VMs or Nodes
    q = Q(status='error', cleared=False)
    vm_type = ContentType.objects.get_for_model(VirtualMachine)
    q &= Q(content_type=vm_type, object_id__in=vms,)
    if admin:
        q |= Q(cluster__in=clusters)
    job_errors = Job.objects.filter(q).order_by("-finished")[:5]
    
    # build list of job errors.  Include jobs from any vm the user has access to
    # If the user has admin on any cluster then those clusters and it's objects
    # must be included too.
    ganeti_errors = GanetiError.objects.get_errors(obj=vms, cleared=False)
    if admin:
        ganeti_errors |= GanetiError.objects.get_errors(obj=clusters, \
                                                        cleared=False)
    
    # merge error lists
    errors = merge_errors(ganeti_errors, job_errors)
    
    # get vm summary
    vms_running = vms.filter(status='running')\
                        .values('cluster__hostname','cluster__slug')\
                        .annotate(running=Count('pk'))
    vms_total = vms.order_by().values('cluster__hostname','cluster__slug') \
                        .annotate(total=Count('pk'))
    vm_summary = {}
    print vms_total
    for cluster in vms_total:
        vm_summary[cluster.pop('cluster__hostname')] = cluster
    for cluster in vms_running:
        vm_summary[cluster['cluster__hostname']]['running'] = cluster['running']
    
    
    # get resources used per cluster
    quota = {}
    owner = user.get_profile()
    owned_vms = VirtualMachine.objects.filter(owner=owner)
    resources = owner.used_resources()
    for cluster in resources.keys():
        quota[cluster] = {
            "used": resources[cluster],
            "set": Cluster.objects.get(pk=cluster).get_quota(owner),
        }
        quota[cluster]["running"] = owned_vms.filter(status="running").count()
        quota[cluster]["total"] = owned_vms.count()
    
    print resources
    
    return render_to_response("overview.html", {
        'admin':admin,
        'cluster_list': clusters,
        'user': request.user,
        'errors': errors,
        'orphaned': orphaned,
        'import_ready': import_ready,
        'missing': missing,
        'resources': quota,
        'vm_summary': vm_summary
        },
        context_instance=RequestContext(request),
    )


@login_required
def clear_ganeti_error(request):
    """
    Clear a single error message
    """
    user = request.user
    error = get_object_or_404(GanetiError, pk=request.POST.get('id', None))
    obj = error.obj
    
    # if not a superuser, check permissions on the object itself
    if not user.is_superuser:
        if isinstance(obj, (Cluster,)) and not user.has_perm('admin', obj):
            return render_403(request, "You do not have sufficient privileges")
        elif isinstance(obj, (VirtualMachine,)):
            # object is a virtual machine, check perms on VM and on Cluster
            if not (obj.owner_id == user.get_profile().pk or \
                user.has_perm('admin', obj.cluster)):
                    return render_403(request, "You do not have sufficient privileges")
    
    # clear the error
    GanetiError.objects.filter(pk=error.pk).update(cleared=True)
    
    return HttpResponse('1', mimetype='application/json')