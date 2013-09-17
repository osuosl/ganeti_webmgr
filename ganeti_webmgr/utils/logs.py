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

from object_log.models import LogAction


def build_vm_cache(user, object1, object2, object3, data):
    """
    object1: VirtualMachine
    object2: Job
    """

    data = {}
    if object1 is not None:
        data['cluster_slug'] = object1.cluster.slug
        data['hostname'] = object1.hostname
        if hasattr(object1, 'newname'):
            data['newname'] = object1.newname
        if object2 is not None:
            data['job_id'] = object2.job_id
    return data


def build_node_cache(user, object1, object2, object3, data):
    data = {}
    if object1 is not None:
        data['cluster_slug'] = object1.cluster.slug
        data['hostname'] = object1.hostname
        if object2 is not None:
            data['job_id'] = object2.job_id
    return data


def build_cluster_cache(user, object1, object2, object3, data):
    data = {}
    if object1 is not None:
        data['cluster_slug'] = object1.slug
        data['hostname'] = object1.hostname
    if object2 is not None:
        data['job_id'] = object2.job_id
    return data


def build_op_cache(user, object1, object2, object3, data):
    data = {
        'object_str': str(object1)
    }
    if object2:
        data['affected_user'] = str(object2)
        data['affected_user_class'] = object2.__class__.__name__
    return data


def register_log_actions():
    # Register LogActions used within the Ganeti App
    LogAction.objects.register('VM_REBOOT', 'ganeti/object_log/vm_reboot.html',
                               build_vm_cache)
    LogAction.objects.register('VM_START', 'ganeti/object_log/vm_start.html',
                               build_vm_cache)
    LogAction.objects.register('VM_STOP', 'ganeti/object_log/vm_stop.html',
                               build_vm_cache)
    LogAction.objects.register('VM_MIGRATE',
                               'ganeti/object_log/vm_migrate.html',
                               build_vm_cache)
    LogAction.objects.register('VM_REPLACE_DISKS',
                               'ganeti/object_log/vm_replace_disks.html',
                               build_vm_cache)
    LogAction.objects.register('VM_REINSTALL',
                               'ganeti/object_log/vm_reinstall.html',
                               build_vm_cache)
    LogAction.objects.register('VM_MODIFY',
                               'ganeti/object_log/vm_modify.html',
                               build_vm_cache)
    LogAction.objects.register('VM_RENAME',
                               'ganeti/object_log/vm_rename.html',
                               build_vm_cache)
    LogAction.objects.register('VM_RECOVER',
                               'ganeti/object_log/vm_recover.html',
                               build_vm_cache)

    LogAction.objects.register('CLUSTER_REDISTRIBUTE',
                               'ganeti/object_log/cluster_redistribute.html',
                               build_cluster_cache)

    LogAction.objects.register('NODE_EVACUATE',
                               'ganeti/object_log/node_evacuate.html',
                               build_node_cache)
    LogAction.objects.register('NODE_MIGRATE',
                               'ganeti/object_log/node_migrate.html',
                               build_node_cache)
    LogAction.objects.register('NODE_ROLE_CHANGE',
                               'ganeti/object_log/node_role_change.html',
                               build_node_cache)

    # add log actions for permission actions here
    LogAction.objects.register('ADD_USER',
                               'ganeti/object_log/permissions/add_user.html',
                               build_op_cache)
    LogAction.objects.register('REMOVE_USER',
                               'ganeti/object_log/permissions'
                               '/remove_user.html',
                               build_op_cache)
    LogAction.objects.register('MODIFY_PERMS',
                               'ganeti/object_log/permissions'
                               '/modify_perms.html',
                               build_op_cache)
