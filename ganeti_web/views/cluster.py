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


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden)
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django_tables2 import SingleTableView

from object_permissions import get_users_any
from object_permissions import signals as op_signals
from object_permissions.views.permissions import view_users, view_permissions

from object_log.models import LogItem
from object_log.views import list_for_object

log_action = LogItem.objects.log_action

from ganeti_web.backend.queries import vm_qs_for_users, cluster_qs_for_user
from ganeti_web.forms.cluster import EditClusterForm, QuotaForm
from ganeti_web.middleware import Http403
from ganeti_web.models import (Cluster, ClusterUser, Profile, SSHKey,
                               VirtualMachine, Job)
from ganeti_web.views import render_404
from ganeti_web.views.generic import (NO_PRIVS, LoginRequiredMixin,
                                      PaginationMixin, GWMBaseView)
from ganeti_web.views.tables import BaseVMTable
from ganeti_web.views.virtual_machine import VMListView
from ganeti_web.util.client import GanetiApiError


class ClusterDetailView(LoginRequiredMixin, DetailView):

    template_name = "ganeti/cluster/detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Cluster, slug=self.kwargs["cluster_slug"])

    def get_context_data(self, **kwargs):
        cluster = kwargs["object"]
        user = self.request.user
        admin = user.is_superuser or user.has_perm("admin", cluster)

        return {
            "cluster": cluster,
            "admin": admin,
            "readonly": not admin,
        }


class ClusterListView(LoginRequiredMixin, PaginationMixin, GWMBaseView,
                      ListView):

    template_name = "ganeti/cluster/list.html"
    default_sort_params = ('hostname', 'asc')
    model = Cluster

    def get_queryset(self):
        self.queryset = cluster_qs_for_user(self.request.user)
        return super(ClusterListView, self).get_queryset()

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(ClusterListView, self).get_context_data(**kwargs)
        context["can_create"]= (user.is_superuser or
                                user.has_perm("admin", Cluster))
        return context


class ClusterVMListView(VMListView):
    table_class = BaseVMTable

    def get_queryset(self):
        self.get_kwargs()
        # Store most of these variables on the object, because we'll be using
        # them in context data too
        self.cluster = get_object_or_404(Cluster, slug=self.cluster_slug)
        # check privs
        self.admin = self.can_create(self.cluster)
        if not self.admin:
            raise Http403(NO_PRIVS)
        self.queryset = vm_qs_for_users(self.request.user, clusters=False)
        # Calling super automatically filters by cluster
        return super(ClusterVMListView, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(ClusterVMListView, self).get_context_data(**kwargs)
        if self.cluster_slug:
            context["cluster"] = self.cluster
            context["create_vm"] = self.admin
            # Required since we cant use a relative link.
            context["ajax_url"] = reverse(
                "cluster-vm-list",
                kwargs={'cluster_slug': self.cluster_slug}
            )
        return context


class ClusterJobListView(LoginRequiredMixin, PaginationMixin, GWMBaseView,
                         ListView):

    template_name = "ganeti/cluster/jobs.html"
    model = Job

    default_sort_params = ('job_id', 'asc')

    def get_queryset(self):
        self.get_kwargs()
        self.cluster = get_object_or_404(Cluster, slug=self.cluster_slug)
        perms = self.can_create(self.cluster)
        if not perms:
            return Http403(NO_PRIVS)

        self.queryset = (Job.objects.filter(cluster__slug=self.cluster_slug)
                                    .select_related("cluster"))
        return super(ClusterJobListView, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(ClusterJobListView, self).get_context_data(**kwargs)
        context['ajax_url'] = reverse(
            'cluster-job-list',
            kwargs={'cluster_slug': self.cluster_slug}
        )
        return context


@login_required
def nodes(request, cluster_slug):
    """
    Display all nodes in a cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)

    # query allocated CPUS for all nodes in this list.  Must be done here to
    # avoid querying Node.allocated_cpus for each node in the list.  Repackage
    # list so it is easier to retrieve the values in the template
    values = VirtualMachine.objects \
        .filter(cluster=cluster, status='running') \
        .exclude(virtual_cpus=-1) \
        .order_by() \
        .values('primary_node') \
        .annotate(cpus=Sum('virtual_cpus'))
    cpus = {}
    nodes = cluster.nodes.all()
    for d in values:
        cpus[d['primary_node']] = d['cpus']

    # Include nodes that do not have any virtual machines on them.
    for node in nodes:
        if node.pk not in cpus:
            cpus[node.pk] = 0

    return render_to_response("ganeti/node/table.html",
                              {'cluster': cluster,
                               'nodes': nodes,
                               'cpus': cpus,
                               },
                              context_instance=RequestContext(request),
                              )


@login_required
def edit(request, cluster_slug=None):
    """
    Edit a cluster
    """
    if cluster_slug:
        cluster = get_object_or_404(Cluster, slug=cluster_slug)
    else:
        cluster = None

    user = request.user
    if not (user.is_superuser or (cluster and user.has_perm(
            'admin', cluster))):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = EditClusterForm(request.POST, instance=cluster)
        if form.is_valid():
            cluster = form.save()
            # TODO Create post signal to import
            #   virtual machines on edit of cluster
            if cluster.info is None:
                try:
                    cluster.sync_nodes()
                    cluster.sync_virtual_machines()
                except GanetiApiError:
                    # ganeti errors here are silently discarded.  It's
                    # valid to enter bad info.  A user might be adding
                    # info for an offline cluster.
                    pass

            log_action('EDIT' if cluster_slug else 'CREATE', user, cluster)

            return HttpResponseRedirect(reverse('cluster-detail',
                                                args=[cluster.slug]))

    elif request.method == 'DELETE':
        cluster.delete()
        return HttpResponse('1', mimetype='application/json')

    else:
        form = EditClusterForm(instance=cluster)

    return render_to_response("ganeti/cluster/edit.html", {
        'form': form,
        'cluster': cluster,
    },
        context_instance=RequestContext(request),
    )


@login_required
def refresh(request, cluster_slug):
    """
    Display a notice to the user that we are refreshing
    the cluster data, then redirect them back to the
    cluster details page.
    """

    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    cluster.sync_nodes(remove=True)
    cluster.sync_virtual_machines(remove=True)

    url = reverse('cluster-detail', args=[cluster.slug])
    return redirect(url)


@login_required
def users(request, cluster_slug):
    """
    Display all of the Users of a Cluster
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)

    url = reverse('cluster-permissions', args=[cluster.slug])
    return view_users(request, cluster, url,
                      template='ganeti/cluster/users.html')


@login_required
def permissions(request, cluster_slug, user_id=None, group_id=None):
    """
    Update a users permissions.
    This wraps object_permissions.view_permissions()
    with our custom permissions checks.
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)

    url = reverse('cluster-permissions', args=[cluster.slug])
    return view_permissions(request, cluster, url, user_id, group_id,
                            user_template='ganeti/cluster/user_row.html',
                            group_template='ganeti/cluster/group_row.html')


@require_POST
@login_required
def redistribute_config(request, cluster_slug):
    """
    Redistribute master-node config to all cluster's other nodes.
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)

    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)

    try:
        job = cluster.redistribute_config()
        job.refresh()
        msg = job.info

        log_action('CLUSTER_REDISTRIBUTE', user, cluster, job)
    except GanetiApiError, e:
        msg = {'__all__': [str(e)]}
    return HttpResponse(json.dumps(msg), mimetype='application/json')


def ssh_keys(request, cluster_slug, api_key):
    """
    Show all ssh keys which belong to users, who have any perms on the cluster
    """
    if settings.WEB_MGR_API_KEY != api_key:
        return HttpResponseForbidden(_("You're not allowed to view keys."))

    cluster = get_object_or_404(Cluster, slug=cluster_slug)

    users = set(get_users_any(cluster).values_list("id", flat=True))
    for vm in cluster.virtual_machines.all():
        users = users.union(set(get_users_any(vm)
                            .values_list('id', flat=True)))

    keys = SSHKey.objects \
        .filter(Q(user__in=users) | Q(user__is_superuser=True)) \
        .values_list('key', 'user__username') \
        .order_by('user__username')

    keys_list = list(keys)
    return HttpResponse(json.dumps(keys_list), mimetype="application/json")


@login_required
def quota(request, cluster_slug, user_id):
    """
    Updates quota for a user
    """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = QuotaForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            cluster_user = data['user']
            if data['delete']:
                cluster.set_quota(cluster_user, None)
            else:
                cluster.set_quota(cluster_user, data)

            # return updated html
            cluster_user = cluster_user.cast()
            url = reverse('cluster-permissions', args=[cluster.slug])
            if isinstance(cluster_user, (Profile,)):
                return render_to_response(
                    "ganeti/cluster/user_row.html",
                    {'object': cluster, 'user_detail': cluster_user.user,
                     'url': url},
                    context_instance=RequestContext(request))
            else:
                return render_to_response(
                    "ganeti/cluster/group_row.html",
                    {'object': cluster, 'group': cluster_user.group,
                     'url': url},
                    context_instance=RequestContext(request))

        # error in form return ajax response
        content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    if user_id:
        cluster_user = get_object_or_404(ClusterUser, id=user_id)
        quota = cluster.get_quota(cluster_user)
        data = {'user': user_id}
        if quota:
            data.update(quota)
    else:
        return render_404(request, _('User was not found'))

    form = QuotaForm(data)
    return render_to_response("ganeti/cluster/quota.html",
                              {'form': form, 'cluster': cluster,
                               'user_id': user_id},
                              context_instance=RequestContext(request))


@login_required
def job_status(request, id, rest=False):
    """
    Return a list of basic info for running jobs.
    """

    ct = ContentType.objects.get_for_model(Cluster)
    jobs = Job.objects.filter(status__in=("error", "running", "waiting"),
                              content_type=ct,
                              object_id=id).order_by('job_id')
    jobs = [j.info for j in jobs]

    if rest:
        return jobs
    else:
        return HttpResponse(json.dumps(jobs), mimetype='application/json')


@login_required
def object_log(request, cluster_slug):
    """ displays object log for this cluster """
    cluster = get_object_or_404(Cluster, slug=cluster_slug)
    user = request.user
    if not (user.is_superuser or user.has_perm('admin', cluster)):
        raise Http403(NO_PRIVS)
    return list_for_object(request, cluster)


def recv_user_add(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_add_user, Logs action
    """
    log_action('ADD_USER', editor, obj, user)


def recv_user_remove(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_remove_user, Logs action
    """
    log_action('REMOVE_USER', editor, obj, user)

    # remove custom quota user may have had.
    if isinstance(user, (User,)):
        cluster_user = user.get_profile()
    else:
        cluster_user = user.organization
    cluster_user.quotas.filter(cluster=obj).delete()


def recv_perm_edit(sender, editor, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_edit_user, Logs action
    """
    log_action('MODIFY_PERMS', editor, obj, user)


op_signals.view_add_user.connect(recv_user_add, sender=Cluster)
op_signals.view_remove_user.connect(recv_user_remove, sender=Cluster)
op_signals.view_edit_user.connect(recv_perm_edit, sender=Cluster)
