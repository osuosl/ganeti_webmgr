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
from ganeti_web.models import Cluster


def site(request):
    """
    Add common site information to the context.
    """

    return {
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SITE_NAME': settings.SITE_NAME,
    }


ANONYMOUS_PERMISSIONS = dict(cluster_admin=False,
                             create_vm=False,
                             view_cluster=False)

CLUSTER_ADMIN_PERMISSIONS = dict(cluster_admin=True,
                             create_vm=True,
                             view_cluster=True)

CLUSTER_VIEW_PERMS = ['migrate', 'export', 'replace_disks', 'tags']


def common_permissions(request):
    """
    Add common cluster permission information to the context.

    Information added by this processor:

        * "cluster_admin" indicates whether the current user is an
          administrator of any clusters.
        * "create_vm" indicates whether the current user is allowed to create
          VMs on any cluster.
        * "view_cluster" indicates whether the current user has any other
          permissions that would allow them to view clusters.
    """

    user = getattr(request, "user", None)

    if user and user.is_authenticated():
        if user.is_superuser:
            return CLUSTER_ADMIN_PERMISSIONS

        perms = user.get_perms_any(Cluster)

        if 'admin' in perms:
            return CLUSTER_ADMIN_PERMISSIONS

        else:
            create_vm = 'create_vm' in perms
            view_cluster = any(p in perms for p in CLUSTER_VIEW_PERMS)

        return {
            'cluster_admin': False,
            'create_vm': create_vm,
            'view_cluster': view_cluster,
        }

    return ANONYMOUS_PERMISSIONS
