# Copyright (c) 2012 Oregon State University
# See license and copying files for copyright information.

# This module provides middleware which Django is too wimpy to provide itself.

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.template import RequestContext, loader

def render_403(request, message):
    """
    Render a 403 response.
    """
    template = loader.get_template('403.html')
    context = RequestContext(request, {
        'message': message,
    })

    return HttpResponseForbidden(template.render(context))


class PermissionDeniedMiddleware(object):
    """
    Middleware which intercepts ``PermissionDenied`` exceptions and returns 403
    responses.
    """

    def process_exception(self, request, e):
        if isinstance(e, PermissionDenied):
            return render_403(request, ", ".join(e.args))
