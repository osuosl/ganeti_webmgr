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

from itertools import chain, izip, repeat

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.generic.base import TemplateView

from object_permissions import get_users_any

from ganeti_web.middleware import Http403
from ganeti_web.models import (Cluster, VirtualMachine, Job, GanetiError,
    ClusterUser, Profile, Organization, SSHKey)
from ganeti_web.views import render_404
from ganeti_web.views.generic import NO_PRIVS
from django.utils.translation import ugettext as _
from ganeti_web.constants import VERSION

from django.core.exceptions import ObjectDoesNotExist
from requests.exceptions import RequestException
from collections import defaultdict

METRICS_ENABLED = True
try:
    from collectd_webdaemon.utils import arbitrary_metrics
    from collectd_webdaemon.models import OverviewCharts
except ImportError:
    METRICS_ENABLED = False


class AboutView(TemplateView):
    template_name = "ganeti/about.html"

    def render_to_response(self, context, **kwargs):
        context["version"] = VERSION
        return super(AboutView, self).render_to_response(context, **kwargs)


def merge_errors(errors, jobs):
    """
    Merge iterables of errors and jobs together.

    The resulting list contains tuples of (bool, object) where the first
    member indicates whether the object is a ``GanetiError`` or ``Job``.
    """

    def keyfunc(x):
        """
        Either the "finished" or "timestamp" attribute.
        """

        return getattr(x[1], "finished", getattr(x[1], "timestamp", 0))

    i = chain(izip(repeat(True), errors), izip(repeat(False), jobs))
    return list(sorted(i, key=keyfunc))


USED_NOTHING = dict(disk=0, ram=0, virtual_cpus=0)


@login_required
def get_errors(request):
    """ Returns all errors that have ever been generated for clusters/vms
    and then sends them to the errors page.
    """
    user = request.user

    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_all_perms(Cluster, ['admin', ])
    admin = user.is_superuser or clusters

    if user.is_superuser:
        vms = VirtualMachine.objects.all()
    else:
        # Get query containing any VMs the user has permissions for
        vms = user.get_objects_any_perms(VirtualMachine, groups=True,
            cluster=['admin']).values('pk')

    # build list of job errors. Include jobs from any vm the user has access to
    # If the user has admin on any cluster then those clusters and it's objects
    # must be included too.
    #
    # XXX all jobs have the cluster listed, filtering by cluster includes jobs
    # for both the cluster itself and any of its VMs or Nodes
    error_clause = Q(status='error')
    vm_type = ContentType.objects.get_for_model(VirtualMachine)
    select_clause = Q(content_type=vm_type, object_id__in=vms)
    if admin:
        select_clause |= Q(cluster__in=clusters)
    job_errors = Job.objects.filter(error_clause & select_clause)

    # Build the list of job errors. Include jobs from any VMs for which the
    # user has access.
    qs = GanetiError.objects
    ganeti_errors = qs.get_errors(obj=vms)
    # If the user is an admin on any cluster, then include administrated
    # clusters and related objects.
    if admin:
        ganeti_errors |= qs.get_errors(obj=clusters)

    # merge error lists
    errors = merge_errors(ganeti_errors, job_errors)

    return render_to_response("ganeti/errors.html", {
        'admin': admin,
        'cluster_list': clusters,
        'user': request.user,
        'errors': errors,
    }, context_instance=RequestContext(request))


def get_used_resources(cluster_user):
    """ help function for querying resources used for a given cluster_user """
    resources = {}
    owned_vms = cluster_user.virtual_machines.all()
    used = cluster_user.used_resources()
    clusters = cluster_user.permissable.get_objects_any_perms(Cluster)
    quotas = Cluster.get_quotas(clusters, cluster_user)

    for cluster, quota in quotas.items():
        resources[cluster] = {
            "used": used.pop(cluster.id) if cluster.id in used else
            USED_NOTHING,
            "set": quota
        }
        resources[cluster]["total"] = owned_vms.filter(cluster=cluster).count()
        resources[cluster]["running"] = owned_vms.filter(cluster=cluster,
                                                    status="running").count()

    # add any clusters that have used resources but no perms (and thus no quota)
    # since we know they don't have a custom quota just add the default quota
    if used:
        for cluster in Cluster.objects.filter(pk__in=used):
            resources[cluster] = {"used": used[cluster.id],
                                  "set": cluster.get_default_quota()}
            resources[cluster]["total"] = owned_vms.filter(cluster=cluster) \
                .count()
            resources[cluster]["running"] = owned_vms.filter(cluster=cluster,
                                                    status="running").count()

    return resources


def update_vm_counts(key, data):
    """
    Updates the cache for numbers of orphaned / ready to import / missing VMs.

    If the cluster's data is not in cache it is ignored.  This is only for
    updating the cache with information we already have.

    @param key - admin data key that is being updated: orphaned,
        ready_to_import, or missing
    @param data - dict of data stored by cluster.pk
    """
    format_key = 'cluster_admin_%d'
    keys = [format_key % k for k in data.keys()]
    cached = cache.get_many(keys)

    for k, v in data.items():
        try:
            values = cached[format_key % k]
            values[key] += v
        except KeyError:
            pass

    cache.set_many(cached, 600)


def get_vm_counts(clusters, timeout=600):
    """
    Helper for getting the list of orphaned/ready to import/missing VMs.
    Caches by the way.

    This caches data under the keys:   cluster_admin_<cluster_id>

    @param clusters the list of clusters, for which numbers of VM are counted.
                    May be None, if update is set.
    @param timeout  specified timeout for cache, in seconds.
    """
    format_key = 'cluster_admin_%d'
    orphaned = import_ready = missing = 0
    cached = cache.get_many((format_key % cluster.pk for cluster in clusters))
    exclude = [int(key[14:]) for key in cached.keys()]
    keys = [k for k in clusters.values_list('pk', flat=True) if k not in
        exclude]
    cluster_list = Cluster.objects.filter(pk__in=keys)

    # total the cached values first
    for k in cached.values():
        orphaned += k["orphaned"]
        import_ready += k["import_ready"]
        missing += k["missing"]

    # update the values that were not cached
    if cluster_list.count():
        base = VirtualMachine.objects.filter(cluster__in=cluster_list,
                owner=None).order_by()
        annotated = base.values("cluster__pk").annotate(orphaned=Count("id"))

        result = {}
        for i in annotated:
            result[format_key % i["cluster__pk"]] = {"orphaned": i["orphaned"]}
            orphaned += i["orphaned"]
        for cluster in cluster_list:
            key = format_key % cluster.pk

            if key not in result:
                result[key] = {"orphaned": 0}

            result[key]["import_ready"] = len(cluster.missing_in_db)
            result[key]["missing"] = len(cluster.missing_in_ganeti)

            import_ready += result[key]["import_ready"]
            missing += result[key]["missing"]

        # add all results into cache
        cache.set_many(result, timeout)

    return orphaned, import_ready, missing


@login_required
def overview(request, rest=False):
    """
    Status page
    """
    user = request.user

    if user.is_superuser:
        clusters = Cluster.objects.all()
    else:
        clusters = user.get_objects_any_perms(Cluster, ['admin', 'create_vm'])
    admin = user.is_superuser or clusters

    #orphaned, ready to import, missing
    if admin:
        # build list of admin tasks for this user's clusters
        orphaned, import_ready, missing = get_vm_counts(clusters)
    else:
        orphaned = import_ready = missing = 0

    if user.is_superuser:
        vms = VirtualMachine.objects.all()
    else:
        # Get query containing any virtual machines the user has permissions for
        vms = user.get_objects_any_perms(VirtualMachine, groups=True,
            cluster=['admin']).values('pk')

    # build list of job errors.  Include jobs from any vm the user has access to
    # If the user has admin on any cluster then those clusters and it's objects
    # must be included too.
    #
    # XXX all jobs have the cluster listed, filtering by cluster includes jobs
    # for both the cluster itself and any of its VMs or Nodes
    error_clause = Q(status='error')
    vm_type = ContentType.objects.get_for_model(VirtualMachine)
    select_clause = Q(content_type=vm_type, object_id__in=vms)
    if admin:
        select_clause |= Q(cluster__in=clusters)
    job_errors = Job.objects.filter(error_clause & select_clause) \
        .order_by("-finished")[:5]

    # Build the list of job errors. Include jobs from any VMs for which the
    # user has access.
    qs = GanetiError.objects.filter(cleared=False)
    ganeti_errors = qs.get_errors(obj=vms)
    # If the user is an admin on any cluster, then include administrated
    # clusters and related objects.
    if admin:
        ganeti_errors |= qs.get_errors(obj=clusters)

    # merge error lists
    errors = merge_errors(ganeti_errors, job_errors)

    # get vm summary - running and totals need to be done as separate queries
    # and then merged into a single list
    vms_running = vms.filter(status='running') \
        .order_by() \
        .values('cluster__hostname', 'cluster__slug') \
        .annotate(running=Count('pk'))
    vms_total = vms.order_by() \
        .values('cluster__hostname', 'cluster__slug') \
        .annotate(total=Count('pk'))
    vm_summary = {}
    for cluster in vms_total:
        vm_summary[cluster.pop('cluster__hostname')] = cluster
    for cluster in vms_running:
        vm_summary[cluster['cluster__hostname']]['running'] = cluster['running']

    # get list of personas for the user:  All groups, plus the user.
    # include the user only if it owns a vm or has perms on at least one cluster
    profile = user.get_profile()
    personas = list(Organization.objects.filter(group__user=user))
    if profile.virtual_machines.count() \
            or user.has_any_perms(Cluster, ['admin', 'create_vm'],
                groups=False) \
            or not personas:
        personas.insert(0, profile)

    # get resources used per cluster from the first persona in the list
    resources = get_used_resources(personas[0])

    create_vm = user.has_perm('create_vm', clusters)

    charts = []
    if METRICS_ENABLED:
        try:
            paths = []
            try:
                obj = OverviewCharts.objects.get(user=request.user)
                paths = json.loads(obj.charts)
            except (ObjectDoesNotExist):
                # should fallback to default list of charts
                pass

            servers = defaultdict(list)
            for path in paths:
                path = path.split("|")
                servers[path[0]].append(path[1])

            for server, path in servers.items():
                chart = arbitrary_metrics(server, path)
                charts.append((server, chart))
        except (RequestException):
            pass

    if rest:
        return clusters
    else:
        return render_to_response("ganeti/overview.html",
            {
                'admin': admin,
                'cluster_list': clusters,
                'create_vm': create_vm,
                'user': request.user,
                'errors': errors,
                'orphaned': orphaned,
                'import_ready': import_ready,
                'missing': missing,
                'resources': resources,
                'vm_summary': vm_summary,
                'personas': personas,
                'charts': charts,
            },
            context_instance=RequestContext(request))


@login_required
def used_resources(request, rest=False):
    """ view for returning used resources for a given cluster user """
    try:
        cluster_user_id = request.GET['id']
    except KeyError:
        return render_404(request, 'requested user was not found')
    cu = get_object_or_404(ClusterUser, pk=cluster_user_id)

    # must be a super user, the user in question, or a member of the group
    user = request.user
    if not user.is_superuser:
        user_type = ContentType.objects.get_for_model(Profile)
        if cu.real_type_id == user_type.pk:
            if not Profile.objects.filter(clusteruser_ptr=cu.pk, user=user)\
                    .exists():
                raise Http403(_('You are not authorized to view this page'))
        else:
            if not Organization.objects.filter(clusteruser_ptr=cu.pk,
                                               group__user=user).exists():
                raise Http403(_('You are not authorized to view this page'))

    resources = get_used_resources(cu.cast())
    if rest:
        return resources
    else:
        return render_to_response("ganeti/overview/used_resources.html", {
            'resources': resources
        }, context_instance=RequestContext(request))


@login_required
def clear_ganeti_error(request, pk):
    """
    Clear a single error message
    """
    user = request.user
    error = get_object_or_404(GanetiError, pk=pk)
    obj = error.obj

    # if not a superuser, check permissions on the object itself
    if not user.is_superuser:
        if isinstance(obj, (Cluster,)) and not user.has_perm('admin', obj):
            raise Http403(NO_PRIVS)
        elif isinstance(obj, (VirtualMachine,)):
            # object is a virtual machine, check perms on VM and on Cluster
            if not (obj.owner_id == user.get_profile().pk or
            user.has_perm('admin', obj.cluster)):
                    raise Http403(NO_PRIVS)

    # clear the error
    GanetiError.objects.filter(pk=error.pk).update(cleared=True)

    return HttpResponse('1', mimetype='application/json')


def ssh_keys(request, api_key):
    """ Lists all keys for all clusters managed by GWM """
    """
    Show all ssh keys which belong to users, who have any perms on the cluster
    """
    if settings.WEB_MGR_API_KEY != api_key:
        return HttpResponseForbidden(_("You're not allowed to view keys."))

    users = set()
    for cluster in Cluster.objects.all():
        users = users.union(set(get_users_any(cluster).values_list("id",
            flat=True)))
    for vm in VirtualMachine.objects.all():
        users = users.union(set(get_users_any(vm).values_list('id',
            flat=True)))

    keys = SSHKey.objects \
        .filter(Q(user__in=users) | Q(user__is_superuser=True)) \
        .values_list('key', 'user__username')\
        .order_by('user__username')

    keys_list = list(keys)
    return HttpResponse(json.dumps(keys_list), mimetype="application/json")
