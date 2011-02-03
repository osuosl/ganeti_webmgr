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

CLUSTER_PARAMS = {
    'perms' : {
        'admin':{
            'label':'Admin',
            'description':'All permissions on this cluster and its virtual machines.  Can grant/revoke permissions.'
        },
        'create_vm':{
            'label':'Create VM',
            'description':'Can create a virtual machine on this cluster.'
        },
        'migrate':{
            'label':'Migrate',
            'description':'Can migrate a virtual machine to another node.'
        },
        'export':{
            'label':'Export',
            'description':'Can export a virtual machine.'
        },
        'replace_disks':{
            'label':'Replace Disks',
            'description':'Can replace the disks of a virtual machines.'
        },
        'tags':{
            'label':'Tags',
            'description':'Can set tags on this cluster.'
        },
    }
}

VIRTUAL_MACHINE_PARAMS = {
    'perms' : {
        'admin':{
            'label':'Admin',
            'description':'All permission on this virtual machine.  Can grant/revoke permissions.'
        },
        'power':{
            'label':'Power',
            'description':'Can start, stop, reboot and access the console.'
        },
        'remove':{
            'label':'Remove',
            'description':'Can delete this virtual machine.'
        },
        'modify':{
            'label':'Modify',
            'description':'Can modify the settings for this virtual machine, including reinstallation'
        },
        'tags':{
            'label':'Tags',
            'description':'Can set tags for this virtual machine.'
        },
    }
}