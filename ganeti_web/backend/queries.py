# Copyright (C) 2012 Oregon State University et al.
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

from django.db.models import Q

from object_permissions import get_users_any, get_groups_any

from ganeti_web.models import Cluster, ClusterUser, VirtualMachine


def cluster_qs_for_user(user, groups=True, readonly=True, **kwargs):
    """
    Return clusters which a user has access to
    """
    if user.is_superuser:
        qs = Cluster.objects.all()
    elif user.is_anonymous():
        qs = Cluster.objects.none()
    else:
        qs = user.get_objects_any_perms(Cluster, ['admin', 'create_vm'],
                                        groups=groups, **kwargs)

    if not readonly:
        # Exclude all read-only clusters.
        qs = qs.exclude(Q(username='') | Q(mtime__isnull=True))

    return qs


def owner_qs_for_cluster(cluster):
    """
    Get all owners for a cluster.
    """

    # get_users_any() can't deal with None, and at any rate, nobody can
    # possibly own a null cluster.
    if not cluster:
        return ClusterUser.objects.none()

    # Get all superusers.
    superusers_qs = ClusterUser.objects.filter(
        profile__user__is_superuser=True)

    # Get all users who have the given permissions on the given cluster.
    # This will include users who's groups have admin privs.
    users = get_users_any(cluster, ["admin"], groups=True)
    # Get the actual groups themselves.
    groups = get_groups_any(cluster, ["admin"])

    qs = ClusterUser.objects.filter(Q(profile__user__in=users) |
                                    Q(organization__group__in=groups))
    qs |= superusers_qs
    return qs.distinct()

def owner_qs(cluster, user):
    if not cluster:
        return ClusterUser.objects.none()

    if user.is_superuser:
        return owner_qs_for_superuser(cluster).order_by('name')

    user_is_admin = user.has_any_perms(cluster, ['admin'], groups=False)

    # Get a list of groups which has admin on this cluster
    admin_groups = get_groups_any(cluster, ["admin"])
    # Get the list of groups the user is in
    users_groups = user.profile.user.groups.all()
    groups = []
    for group in users_groups:
        # filter out the groups the user isn't in
        if group in admin_groups:
            groups.append(group)

    # The groups the user is in
    groups_q = Q(organization__group__in=groups)
    if user_is_admin:
        # User is admin, so we want to include them.
        qs =  ClusterUser.objects.filter(Q(profile__user=user) | groups_q)
    else:
        qs = ClusterUser.objects.filter(groups_q)

    return qs.order_by('name')


def owner_qs_for_superuser(cluster):
    "Return all the users since we are superuser"
    return ClusterUser.objects.all()

def vm_qs_for_admins(user):
    """
    Retrieve a queryset of all of the virtual machines for which this user is
    an administrator.
    """

    if user.is_superuser:
        qs = VirtualMachine.objects.all()
    elif user.is_anonymous():
        qs = VirtualMachine.objects.none()
    else:
        qs = user.get_objects_any_perms(VirtualMachine, groups=True,
                                        perms=["admin"])

    return qs


def vm_qs_for_users(user, clusters=True):
    """
    Retrieves a queryset of all the virtual machines for which the user has
    any permission.
    """

    if user.is_superuser:
        qs = VirtualMachine.objects.all()
    elif user.is_anonymous():
        qs = VirtualMachine.objects.none()
    else:
        # If no permissions are provided, then *any* permission will cause a VM
        # to be added to the query.
        qs = user.get_objects_any_perms(VirtualMachine, groups=True)

        # Add all VMs including VMs you have permission to via Cluster Perms
        if clusters:
            # first we get the IDs of the clusters which a user is admin of
            cluster_ids = user.get_objects_any_perms(
                Cluster, ['admin'], groups=True).values_list('pk', flat=True)
            # next create a queryset of VMs where the user is an admin of the
            # cluster
            cluster_vm_qs = VirtualMachine.objects.filter(
                cluster__pk__in=cluster_ids).distinct()

            # Union of vms a user has any permissions to AND vms a user has
            # permissions to via cluster
            qs |= cluster_vm_qs

    return qs.distinct()
