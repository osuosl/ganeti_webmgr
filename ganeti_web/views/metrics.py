# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext

import simplejson as json

from collectd_webdaemon.utils import metrics_tree, arbitrary_metrics

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
        tree = metrics_tree(DAEMON_HOST)
        return render_to_response("ganeti/metrics/general.html",
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
    return render_to_response("ganeti/metrics/node.html",
        {
        },
        context_instance=RequestContext(request)
    )


@login_required
def metrics_vm(request, vm):
    """
    Displays metrics for a particular virtual machine.
    This view is reachable from Virtual Machine overview page.
    """
    return render_to_response("ganeti/metrics/virtual_machine.html",
        {},
        context_instance=RequestContext(request)
    )
