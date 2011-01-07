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


from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
#from object_permissions import get_model_perms, get_user_perms, grant, revoke, \
#    get_users, get_groups, get_group_perms
from ganeti.models import Cluster


@login_required
def index(request):
    user = request.user

    # should be more complex query in future
    # like: user.is_admin_on_any(Cluster)
    if (user.is_superuser or user.has_any_perms(Cluster, ["admin",])):
        return HttpResponseRedirect(reverse("cluster-overview"))
    else:
        return HttpResponseRedirect(reverse("virtualmachine-list"))
