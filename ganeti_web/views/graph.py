from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden, HttpResponseBadRequest,
                         Http404)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from django.views.generic import TemplateView

from object_log.views import list_for_object

from object_permissions import get_users_any
from object_permissions.signals import (view_add_user, view_edit_user,
                                        view_remove_user)
from object_permissions.views.permissions import view_users, view_permissions

from object_log.models import LogItem
log_action = LogItem.objects.log_action

from ganeti_web.middleware import Http403
from ganeti_web.models import Cluster, Node, VirtualMachine
from ganeti_web.templatetags.webmgr_tags import render_storage
from ganeti_web.util.client import GanetiApiError
from ganeti_web.utilities import (cluster_os_list, compare, os_prettify,
                                  get_hypervisor)
from ganeti_web.views.generic import (NO_PRIVS, LoginRequiredMixin,
                                      PagedListView)


class ClusterGraphView(LoginRequiredMixin, TemplateView):
    """
    View for generating a graph representing a Ganeti Cluster.
    """
    template_name = "graph/graph_object.js"
    cluster_hostname = "ganeti.example.org"
    cluster = Cluster.objects.get(hostname=cluster_hostname)
    vms = VirtualMachine.objects.filter(cluster=cluster)

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super(ClusterGraphView, self).get_context_data(** kwargs)
        context['vm_queryset'] = self.vms
        return context

