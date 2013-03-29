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
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from object_log.models import LogItem
from object_log.views import list_for_object

log_action = LogItem.objects.log_action

from ganeti_web.util.client import GanetiApiError
from ganeti_web import constants
from ganeti_web.forms.node import RoleForm, MigrateForm, EvacuateForm
from ganeti_web.middleware import Http403
from ganeti_web.models import Node, Job
from ganeti_web.views.generic import (NO_PRIVS, LoginRequiredMixin,
                                      PaginationMixin, SortingMixin)


def get_node_and_cluster_or_404(cluster_slug, host):
    """
    Utility function for querying Node and Cluster in a single query
    rather than 2 separate calls to get_object_or_404.
    """
    query = Node.objects \
        .filter(cluster__slug=cluster_slug, hostname=host) \
        .select_related('cluster')
    if len(query):
        return query[0], query[0].cluster
    raise Http404('Node does not exist')


class NodeDetailView(LoginRequiredMixin, DetailView):

    template_name = "ganeti/node/detail.html"

    def get_object(self, queryset=None):
        self.node, self.cluster = get_node_and_cluster_or_404(
            self.kwargs["cluster_slug"], self.kwargs["host"])
        return self.node

    def get_context_data(self, **kwargs):
        user = self.request.user
        admin = user.is_superuser or user.has_perm('admin', self.cluster)
        modify = admin or user.has_perm('migrate', self.cluster)
        readonly = not (admin or modify)

        return {
            "cluster": self.cluster,
            "node_count": self.cluster.nodes.all().count(),
            "node": self.node,
            "admin": admin,
            "modify": modify,
            "readonly": readonly,
        }


class NodePrimaryListView(LoginRequiredMixin, PaginationMixin, ListView):
    """
    Renders a list of primary VirtualMachines on the given node.
    """

    template_name = "ganeti/virtual_machine/table.html"

    def get_queryset(self):
        self.node, self.cluster = get_node_and_cluster_or_404(
            self.kwargs["cluster_slug"], self.kwargs["host"])

        user = self.request.user
        if not (user.is_superuser or
                user.has_any_perms(self.cluster, ["admin", "migrate"])):
            raise Http403(NO_PRIVS)

        return self.node.primary_vms.all()

    def get_context_data(self, **kwargs):
        kwargs.update({
            "tableID": "table_primary",
            "primary_node": True,
            "node": self.node,
        })
        return kwargs


class NodeSecondaryListView(LoginRequiredMixin, PaginationMixin, ListView):
    """
    Renders a list of secondary VirtualMachines on the given node.
    """

    template_name = "ganeti/virtual_machine/table.html"

    def get_queryset(self):
        self.node, self.cluster = get_node_and_cluster_or_404(
            self.kwargs["cluster_slug"], self.kwargs["host"])

        user = self.request.user
        if not (user.is_superuser or
                user.has_any_perms(self.cluster, ["admin", "migrate"])):
            raise Http403(NO_PRIVS)

        return self.node.secondary_vms.all()

    def get_context_data(self, **kwargs):
        kwargs.update({
            "tableID": "table_secondary",
            "secondary_node": True,
            "node": self.node,
        })
        return kwargs


@login_required
def object_log(request, cluster_slug, host, rest=False):
    """
    Display object log for this node
    """
    node, cluster = get_node_and_cluster_or_404(cluster_slug, host)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster,
                                                    ['admin', 'migrate'])):
        if not rest:
            raise Http403(NO_PRIVS)
        else:
            return {'error': NO_PRIVS}

    return list_for_object(request, node, rest)


@login_required
def role(request, cluster_slug, host):
    """
    view used for setting node role
    """
    node, cluster = get_node_and_cluster_or_404(cluster_slug, host)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster,
                                                    ['admin', 'migrate'])):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            try:
                job = node.set_role(form.cleaned_data['role'])
                job.refresh()
                msg = job.info

                # log information
                log_action('NODE_ROLE_CHANGE', user, node)
                return HttpResponse(json.dumps(msg),
                                    mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__': [str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    elif node.role == 'M':
        # XXX master isn't a possible choice for changing role
        form = RoleForm()

    else:
        data = {'role': constants.ROLE_MAP[node.role]}
        form = RoleForm(data)

    return render_to_response('ganeti/node/role.html',
                              {'form': form, 'node': node, 'cluster': cluster},
                              context_instance=RequestContext(request))


@login_required
def migrate(request, cluster_slug, host):
    """
    view used for initiating a Node Migrate job
    """
    node, cluster = get_node_and_cluster_or_404(cluster_slug, host)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster,
                                                    ['admin', 'migrate'])):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = MigrateForm(request.POST)
        if form.is_valid():
            try:
                job = node.migrate(form.cleaned_data['mode'])
                job.refresh()
                msg = job.info

                # log information
                log_action('NODE_MIGRATE', user, node)

                return HttpResponse(json.dumps(msg),
                                    mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__': [str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    else:
        form = MigrateForm()

    return render_to_response('ganeti/node/migrate.html',
                              {'form': form, 'node': node, 'cluster': cluster},
                              context_instance=RequestContext(request))


@login_required
def evacuate(request, cluster_slug, host):
    """
    view used for initiating a node evacuate job
    """
    node, cluster = get_node_and_cluster_or_404(cluster_slug, host)

    user = request.user
    if not (user.is_superuser or user.has_any_perms(cluster,
                                                    ['admin', 'migrate'])):
        raise Http403(NO_PRIVS)

    if request.method == 'POST':
        form = EvacuateForm(cluster, node, request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                evacuate_node = data['node']
                iallocator_hostname = data['iallocator_hostname']
                job = node.evacuate(iallocator_hostname, evacuate_node)
                job.refresh()
                msg = job.info

                # log information
                log_action('NODE_EVACUATE', user, node, job)

                return HttpResponse(json.dumps(msg),
                                    mimetype='application/json')
            except GanetiApiError, e:
                content = json.dumps({'__all__': [str(e)]})
        else:
            # error in form return ajax response
            content = json.dumps(form.errors)
        return HttpResponse(content, mimetype='application/json')

    else:
        form = EvacuateForm(cluster, node)

    return render_to_response('ganeti/node/evacuate.html',
                              {'form': form, 'node': node, 'cluster': cluster},
                              context_instance=RequestContext(request))


@login_required
def job_status(request, id, rest=False):
    """
    Return a list of basic info for running jobs.
    """
    ct = ContentType.objects.get_for_model(Node)
    jobs = Job.objects.filter(status__in=("error", "running", "waiting"),
                              content_type=ct,
                              object_id=id).order_by('job_id')
    jobs = [j.info for j in jobs]

    if rest:
        return jobs
    else:
        return HttpResponse(json.dumps(jobs), mimetype='application/json')
