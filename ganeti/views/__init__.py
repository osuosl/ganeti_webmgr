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

from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.template import RequestContext
from django.template import Context, loader


def render_403(request, message):
    """
    Render a 403 response
    """
    template = loader.get_template('403.html')
    context = RequestContext(request, {
        'message': message,
    })
    return HttpResponseForbidden(template.render(context))


def render_404(request, message):
    """
    Render a 404 response
    """
    template = loader.get_template('404.html')
    context = RequestContext(request)
    return HttpResponseNotFound(template.render(context))


def view_500(request):
    template = loader.get_template('500.html')
    context = RequestContext(request)
    return HttpResponseNotFound(template.render(context))