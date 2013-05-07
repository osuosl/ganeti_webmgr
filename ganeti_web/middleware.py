# Copyright (c) 2012 Oregon State University
# See license and copying files for copyright information.

# This module provides middleware which Django is too wimpy to provide itself.

from django.http import HttpResponseForbidden
from django.template import RequestContext, loader


class Http403(Exception):
    """
    A 403 error should be sent back to our client.
    """


def render_403(request, message):
    """
    Render a 403 response.
    """

    template = loader.get_template('403.html')
    context = RequestContext(request, {
        'message': message,
    })

    return HttpResponseForbidden(template.render(context))


class Http403Middleware(object):
    """
    Middleware which intercepts ``Http403`` exceptions and returns 403
    responses.
    """

    def process_exception(self, request, e):
        if isinstance(e, Http403):
            return render_403(request, ", ".join(e.args))
