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

from django.conf import settings
from ganeti.models import Cluster


def site(request):
    """
    adds site properties to the context
    """    
    return {'SITE_DOMAIN':settings.SITE_DOMAIN, 'SITE_NAME':settings.SITE_NAME}


ANONYMOUS_PERMISSIONS = dict(cluster_admin=False, create_vm=False)

def common_permissions(request):
    """
    adds common cluster perms to the context:

        * cluster admin
        * create vm
    """
    user = request.user
    if user.is_authenticated():
        if user.is_superuser:
            cluster_admin = create_vm = True
        else:
            cluster_admin = user.has_any_perms(Cluster, ['admin'])
            if cluster_admin:
                create_vm = True
            else:
                create_vm = user.has_any_perms(Cluster, ['create_vm'])

        return {
            'cluster_admin':cluster_admin,
            'create_vm':create_vm
        }

    return ANONYMOUS_PERMISSIONS