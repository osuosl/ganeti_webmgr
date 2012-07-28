# coding: utf-8
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

import simplejson as json

from collectd_webdaemon.utils import (metrics_tree, arbitrary_metrics,
    similar_thresholds, all_thresholds, add_threshold, edit_threshold,
    get_threshold, delete_threshold)

DAEMON_HOST = 'http://node1.example.org:8888'


@login_required
def metrics_general(request):
    """
    On GET request it simply displays general interface to access any host, any
    plugin and any type of metrics that are stored.

    On POST request it returns metrics for specified set of hosts/plugins/types
    (from GET request.)
    """
    if request.method == "GET":
        tree = metrics_tree(DAEMON_HOST).json["tree"]
        return render_to_response("ganeti/metrics/metrics_general.html",
            {
                "tree": tree,
                # I need JSONified list, because I'm using it in JavaScript
                "tree_json": json.dumps(tree),
            },
            context_instance=RequestContext(request)
        )

    elif request.method == "POST":
        paths = request.POST.getlist("paths[]")  # jQuery appends '[]'
        start = request.POST.get("start", "-1h")
        end = request.POST.get("end", "now")

        chart = arbitrary_metrics(DAEMON_HOST, paths, start, end)

        return render_to_response("ganeti/metrics/metrics_display.html",
            {
                "metrics": chart,
            },
            context_instance=RequestContext(request)
        )


@login_required
def metrics_node(request, node):
    """
    Displays metrics for this particular node.
    This view is reachable from Node overview page.
    """
    # TODO: display also for node's all virtual machines?
    return render_to_response("ganeti/metrics/metrics_node.html",
        {},
        context_instance=RequestContext(request)
    )


@login_required
def metrics_vm(request, vm):
    """
    Displays metrics for a particular virtual machine.
    This view is reachable from Virtual Machine overview page.
    """
    return render_to_response("ganeti/metrics/metrics_virtual_machine.html",
        {},
        context_instance=RequestContext(request)
    )


@login_required
def thresholds_general(request, host=None, plugin=None, type=None):
    """
    General UI for changing thresholds.

    If arguments are provided, it will display a UI specifically for changing
    given thresholds or similar thresholds.
    """
    if any([host, plugin, type]):
        # for the beginning we display similar thresholds if they exist.
        # Otherwise we display form to add new threshold.
        results = similar_thresholds(DAEMON_HOST, str(host), str(plugin),
            str(type))

        return render_to_response("ganeti/metrics/thresholds_display.html",
            results.json,
            context_instance=RequestContext(request))
    else:
        result = all_thresholds(DAEMON_HOST)
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
    if request.method == "POST":
        form = ThresholdForm(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            result = add_threshold(DAEMON_HOST, data)
            if result.status_code in [200, 201]:
                # success :)
                messages.success(request, _("New threshold was created."))
                return HttpResponseRedirect(reverse("thresholds-general"))
            else:
                # oops :(
                messages.error(request, _("Threshold could not be created."))
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
    if request.method == "POST":
        form = ThresholdForm(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            result = edit_threshold(DAEMON_HOST, threshold_id, data)
            if result.status_code == 200:
                # success :)
                messages.success(request, _("The threshold was updated."))
                return HttpResponseRedirect(reverse("thresholds-general"))
            else:
                # oops :(
                messages.error(request, _("Threshold could not be updated."))
        else:
            messages.error(request, _("This form contains errors."))
    else:
        result = get_threshold(DAEMON_HOST, threshold_id)
        if result.status_code != 200:
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
    result = delete_threshold(DAEMON_HOST, threshold_id)

    if result.status_code == 200:
        messages.success(request, _("The threshold was successfully deleted."))
    else:
        messages.error(request, _("Could not delete that threshold."))

    return HttpResponseRedirect(reverse("thresholds-general"))
