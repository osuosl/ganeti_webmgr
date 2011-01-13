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
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.contenttypes.models import ContentType
#from object_permissions import get_model_perms, get_user_perms, grant, revoke, \
#    get_users, get_groups, get_group_perms
from ganeti.models import Cluster, VirtualMachine, Job, GanetiError


@login_required
def index(request):
    user = request.user

    # should be more complex query in future
    # like: user.is_admin_on_any(Cluster)
    if (user.is_superuser or user.has_any_perms(Cluster, ["admin",])):
        return HttpResponseRedirect(reverse("cluster-overview"))
    else:
        return HttpResponseRedirect(reverse("virtualmachine-list"))


@login_required
def overview(request):
    """
    Status page
    """
    user = request.user

    admin = True
    if user.is_superuser:
        cluster_list = Cluster.objects.all()

    else:
        cluster_list = user.get_objects_all_perms(Cluster, ['admin',],
            groups=True)

        if not cluster_list:
            #return HttpResponseForbidden('You do not have sufficient privileges')
            admin = False

    if admin:
        vms = VirtualMachine.objects.filter(owner=user.get_profile())
        #vms = None

        #ganeti errors
        ganeti_errors = GanetiError.objects.get_errors(clusters=cluster_list,
            cleared=False)

        job_errors = Job.objects.filter(cluster__in=cluster_list, status="error"). \
                order_by("-finished")[:5]

        #orphaned
        orphaned = VirtualMachine.objects.filter(owner=None,
                cluster__in=cluster_list).count()

        #ready for import vms
        import_ready = 0

        #missing vms
        missing = 0

        for cluster in cluster_list:
            import_ready += len(cluster.missing_in_db)
            missing += len(cluster.missing_in_ganeti)

    else:
        #vms = user.get_objects_any_perms(VirtualMachine, groups=True)
        vms = VirtualMachine.objects.filter(owner=user.get_profile())

        #ganeti errors
        ganeti_errors = GanetiError.objects.get_errors(vms=vms, cleared=False)

        # content type of VirtualMachine model
        # NOTE: done that way because if behavior of GenericForeignType
        #       i.e. Django doesn't allow to filter on GenericForeignType
        vm_type = ContentType.objects.get_for_model(VirtualMachine)
        job_errors = Job.objects.filter( content_type=vm_type, object_id__in=vms,
                status="error" ).order_by("finished")[:5]

        #orphaned, ready to import, missing
        orphaned = import_ready = missing = 0

    quota = {}
    owner = user.get_profile()
    resources = owner.used_resources()
    for cluster in resources.keys():
        quota[cluster] = {
            "used": resources[cluster],
            "set": Cluster.objects.get(pk=cluster).get_quota(owner),
        }
        #if vms:
        quota[cluster]["running"] = vms.filter(status="running").count()
        quota[cluster]["total"] = vms.count()

    return render_to_response("overview.html", {
        'admin':admin,
        'cluster_list': cluster_list,
        'user': request.user,
        'ganeti_errors': ganeti_errors,
        'job_errors': job_errors,
        'orphaned': orphaned,
        'import_ready': import_ready,
        'missing': missing,
        'resources': quota,
        },
        context_instance=RequestContext(request),
    )
