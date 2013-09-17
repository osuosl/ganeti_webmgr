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

from django.http import HttpResponseNotFound
from django.template import RequestContext, loader


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
