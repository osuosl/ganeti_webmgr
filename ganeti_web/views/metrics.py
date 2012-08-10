# coding: utf-8
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf import settings

from collections import defaultdict
import simplejson as json
from requests.exceptions import RequestException
from .virtual_machine import get_vm_and_cluster_or_404


METRICS_ENABLED = True
try:
    from collectd_webdaemon.utils import (metrics_tree, metrics_hosts,
        arbitrary_metrics, similar_thresholds, all_thresholds, add_threshold,
        edit_threshold, get_threshold, delete_threshold)
    from collectd_webdaemon.models import OverviewCharts
except ImportError:
    METRICS_ENABLED = False


def check_configured_hosts(settings):
    """
    Auxiliary function. Tests if defined metrics host is correct.

    :param settings: Django settings
    """
    hosts = []

    if not hasattr(settings, "METRICS_DAEMON"):
        return False
    elif not settings.METRICS_DAEMON:
        return False
    elif type(settings.METRICS_DAEMON) is list:
        hosts += settings.METRICS_DAEMON
    elif settings.METRICS_DAEMON == "node":
        return "node"
    else:
        hosts.append(settings.METRICS_DAEMON)

    try:
        from urllib.parse import urlparse
    except ImportError:
        from urlparse import urlparse

    for host in hosts:
        url = urlparse(host)
        if not all([url.scheme, url.hostname]) or url.path:
            return False
    return hosts if len(hosts) > 1 else hosts[0]


DAEMON_HOST = check_configured_hosts(settings)
METRICS_ENABLED = bool(DAEMON_HOST)


def get_hosts(var):
    """
    Get list of hosts based on configuration.
    TODO: cache query
    """
    hosts = []
    if type(var) is list:
        hosts = var[:]
    elif var == "node":
        from ganeti_web.models import Node
        result = Node.objects.values_list("hostname")
        hosts = [x[0] for x in list(result)]
    else:
        hosts.append(var)
    return hosts


# this decorator's here just in case someone accidentially added
# 'error_spotted' to the urls.py
@login_required
def error_spotted(request, msg, template, data=None):
    """
    This view is supposed to be returned whenever an exception is caught.

    :param msg: message content. The message will be shown using Django's very
                own messages system.
    :param template: path to the template used.
    :param data: dictionary of data given to the template.
    """
    messages.error(request, msg)
    return render_to_response(template, data or dict(),
        context_instance=RequestContext(request))


def metrics_disabled(request):
    """
    This is a fallback view, displayed whenever metrics support is disabled.
    """
    return render_to_response("ganeti/metrics/disabled.html", {},
        context_instance=RequestContext(request))


@login_required
def metrics_general(request):
    """
    On GET request it simply displays general interface to access any host, any
    plugin and any type of metrics that are stored.

    On POST request it returns metrics for specified set of hosts/plugins/types
    (from GET request.)
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    if request.method == "GET":
        template = "ganeti/metrics/metrics_general.html"

        hosts = get_hosts(DAEMON_HOST)

        tree = dict()
        for host in hosts:
            try:
                tree[host] = metrics_tree(host).json["tree"]
            except (RequestException, KeyError, TypeError):
                return error_spotted(request,
                    _("Couldn't connect to the metrics host %s") %
                    host, template)

        return render_to_response(template,
            {
                "nodes": type(DAEMON_HOST) is list,
                "tree": tree,
                # I need JSONified list, because I'm using it in JavaScript
                "tree_json": json.dumps(tree),
                "metrics_paths": request.session.get("metrics_paths", tuple()),
            },
            context_instance=RequestContext(request)
        )

    elif request.method == "POST":
        paths = request.POST.getlist("paths[]")  # jQuery appends '[]'
        start = request.POST.get("start", "-1h")
        end = request.POST.get("end", "now")

        request.session["metrics_paths"] = tuple(paths)

        template = "ganeti/metrics/metrics_display.html"

        servers = defaultdict(list)
        for path in paths:
            path = path.split("|")
            servers[path[0]].append(path[1])

        # many charts. They have titles, too
        charts = []
        for server, path in servers.items():
            try:
                chart = arbitrary_metrics(server, path, start, end)
                charts.append((server, chart))
            except (RequestException):
                return error_spotted(request,
                    _("Couldn't obtain specified metrics."), template)

        return render_to_response(template,
            {
                "nodes": type(DAEMON_HOST) is list,
                "charts": charts,
            },
            context_instance=RequestContext(request)
        )


@login_required
def metrics_node(request, cluster_slug, host):
    """
    Displays metrics for this particular node.
    This view is reachable from Node overview page.
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    template = "ganeti/metrics/metrics_node.html"

    metrics_server = ""
    tree = None
    servers = get_hosts(DAEMON_HOST)
    try:
        for server in servers:
            if host in metrics_hosts(server).json["hosts"]:
                tree = metrics_tree(server).json["tree"]
                metrics_server = server
                break
    except (RequestException, KeyError, TypeError):
        return error_spotted(request,
            _("Couldn't obtain the list of hosts or host's metrics tree."),
            template)

    if tree:
        return render_to_response("ganeti/metrics/metrics_node_vm.html",
            {
                "server": metrics_server,
                "host": host,
                "tree": tree[host],
                "tree_json": json.dumps(tree[host]),
            },
            context_instance=RequestContext(request)
        )
    else:
        return error_spotted(request,
            _("Couldn't find this host on any metrics server."), template)


@login_required
def metrics_vm(request, cluster_slug, instance):
    """
    Displays metrics for a particular virtual machine.
    This view is reachable from Virtual Machine overview page.
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    template = "ganeti/metrics/metrics_node.html"
    vm, cluster = get_vm_and_cluster_or_404(cluster_slug, instance)

    host = "%s_%s" % (cluster.info["default_hypervisor"], instance)

    metrics_server = ""
    tree = None
    servers = get_hosts(DAEMON_HOST)
    try:
        for server in servers:
            if host in metrics_hosts(server).json["hosts"]:
                tree = metrics_tree(server).json["tree"]
                metrics_server = server
                break
    except (RequestException, KeyError, TypeError):
        return error_spotted(request,
            _("Couldn't obtain the list of hosts or host's metrics tree."),
            template)

    if tree:
        return render_to_response("ganeti/metrics/metrics_node_vm.html",
            {
                "server": metrics_server,
                "host": host,
                "tree": tree[host],
                "tree_json": json.dumps(tree[host]),
            },
            context_instance=RequestContext(request)
        )
    else:
        return error_spotted(request,
            _("Couldn't find this host on any metrics server."), template)


@login_required
def save_overview(request):
    """
    Saves provided (via POST) list of paths so that they're displayed on the
    overview page.
    """
    data = request.POST.getlist("paths[]")
    obj = OverviewCharts(user=request.user, charts=json.dumps(data))
    obj.save()
    return HttpResponse("OK")


@login_required
def thresholds_general(request, host=None, plugin=None, type=None):
    """
    General UI for changing thresholds.

    If arguments are provided, it will display a UI specifically for changing
    given thresholds or similar thresholds. Otherwise it'll display a list of
    all defined thresholds.
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    if type:
        type = type.replace(".rrd", "")

    if any([host, plugin, type]):
        # for the beginning we display similar thresholds if they exist.
        # Otherwise we display form to add new threshold.
        try:
            result = similar_thresholds(DAEMON_HOST, str(host), str(plugin),
                str(type))
        except RequestException:
            return error_spotted(request,
                _("Couldn't obtain any threshold from %s") %
                DAEMON_HOST, "ganeti/metrics/thresholds_general.html")

        if "thresholds" in result.json.keys() and len(
                result.json["thresholds"]):
            return render_to_response(
                "ganeti/metrics/thresholds_display.html",
                result.json,
                context_instance=RequestContext(request))
        else:
            # 3) add new threshold
            plugin = plugin.split("-")
            type = type.split("-")
            form = ThresholdForm(initial={
                "host": host,
                "plugin": plugin[0],
                "type": type[0],
                "plugin_instance": plugin[1] if len(plugin) >= 2 else "",
                "type_instance": type[1] if len(type) >= 2 else "",
            })

            return render_to_response("ganeti/metrics/threshold_form.html",
                {"form": form, "action": "add"},
                context_instance=RequestContext(request))
    else:
        try:
            result = all_thresholds(DAEMON_HOST)
        except RequestException:
            return error_spotted(request,
                _("Couldn't obtain the list of thresholds from %s") %
                DAEMON_HOST, "ganeti/metrics/thresholds_general.html")

        return render_to_response("ganeti/metrics/thresholds_general.html",
            result.json,
            context_instance=RequestContext(request))


class ThresholdForm(forms.Form):
    host = forms.CharField(max_length=50, required=False)
    plugin = forms.CharField(max_length=50, required=False)
    plugin_instance = forms.CharField(max_length=50, required=False)
    type = forms.CharField(max_length=50, required=True)
    type_instance = forms.CharField(max_length=50, required=False)
    datasource = forms.CharField(max_length=50, required=False)
    warning_min = forms.FloatField(required=False)
    warning_max = forms.FloatField(required=False)
    failure_min = forms.FloatField(required=False)
    failure_max = forms.FloatField(required=False)
    percentage = forms.BooleanField(required=False)
    persist = forms.BooleanField(required=False)
    invert = forms.BooleanField(required=False)
    hits = forms.IntegerField(required=False)
    hysteresis = forms.BooleanField(required=False)


@login_required
def threshold_add(request):
    """
    Adds a new threshold through the form.
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    if request.method == "POST":
        form = ThresholdForm(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            try:
                result = add_threshold(DAEMON_HOST, data)
                if result.status_code not in [200, 201]:
                    raise RuntimeError("Wrong status code.")
            except (RequestException, RuntimeError):
                messages.error(request, _("Threshold could not be created."))
            else:
                messages.success(request, _("New threshold was created."))
                return HttpResponseRedirect(reverse("thresholds-general"))

        else:
            messages.error(request, _("This form contains errors."))
    else:
        form = ThresholdForm()

    return render_to_response("ganeti/metrics/threshold_form.html",
        {"form": form, "action": "add"},
        context_instance=RequestContext(request))


@login_required
def threshold_edit(request, threshold_id):
    """
    Changes a threshold through the form.
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    if request.method == "POST":
        form = ThresholdForm(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            try:
                result = edit_threshold(DAEMON_HOST, threshold_id, data)
                if result.status_code != 200:
                    raise RuntimeError("Wrong status code.")
            except (RequestException, RuntimeError):
                messages.error(request, _("Threshold could not be updated."))
            else:
                messages.success(request, _("The threshold was updated."))
                return HttpResponseRedirect(reverse("thresholds-general"))
        else:
            messages.error(request, _("This form contains errors."))
    else:
        try:
            result = get_threshold(DAEMON_HOST, threshold_id)
            if result.status_code != 200:
                raise RuntimeError("Wrong status code.")
            result.json["threshold"]
        except (RequestException, RuntimeError, KeyError):
                messages.error(request, _("There's no such threshold."))
                return HttpResponseRedirect(reverse("thresholds-general"))

        form = ThresholdForm(initial=result.json["threshold"])

    return render_to_response("ganeti/metrics/threshold_form.html",
        {"form": form, "action": "edit"},
        context_instance=RequestContext(request))


@login_required
def threshold_delete(request, threshold_id):
    """
    Removes specified threshold.
    Doesn't ask for confirmation. Confirmation should be obtained before.
    """
    if not METRICS_ENABLED:
        return metrics_disabled(request)

    try:
        result = delete_threshold(DAEMON_HOST, threshold_id)
        if result.status_code == 200:
            raise RuntimeError("Wrong status code.")
    except (RequestException, RuntimeError):
        messages.error(request, _("Could not delete that threshold."))
    else:
        messages.success(request, _("The threshold was successfully deleted."))

    return HttpResponseRedirect(reverse("thresholds-general"))
