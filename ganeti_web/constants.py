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

VERSION = '0.9'
OWNER_TAG = 'gwm:owner:'

# Form Constants
EMPTY_CHOICE_FIELD = (u'', u'---------')

MODE_CHOICES = (
    ('live','Live'),
    ('non-live','Non-Live'),
)

NODE_ROLE_MAP = {
    'M':'Master',
    'C':'Master Candidate',
    'R':'Regular',
    'D':'Drained',
    'O':'Offline',
}

ROLE_CHOICES = (
    EMPTY_CHOICE_FIELD,
    (u'master-candidate',u'Master Candidate'),
    (u'regular',u'Regular'),
    (u'drained',u'Drained'),
    (u'offline',u'Offline'),
)

ROLE_MAP = {
    'C':u'master-candidate',
    'R':u'regular',
    'D':u'drained',
    'O':u'offline',
}

# KVM Choices
KVM_BOOT_ORDER = [
    (u'disk', u'Hard Disk'),
    (u'cdrom', u'CD-ROM'),
    (u'network', u'Network'),
]

KVM_FLAGS = [
    EMPTY_CHOICE_FIELD,
    (u'enabled', u'Enabled'),
    (u'disabled', u'Disabled'),
]

KVM_DISK_TYPES = [
    (u'scsi', u'SCSI'),
    (u'sd', u'SD Card'),
    (u'mtd', u'MTD'),
    (u'pflash', u'PC System Flash'),
]

KVM_NIC_TYPES = [
    (u'i82551',u'i82551'),
    (u'i82557b',u'i82557B'),
    (u'i82559er',u'i82559ER'),
    (u'pcnet',u'PCnet'),
]

# Xen HVM Choices
HVM_BOOT_ORDER = [
    (u'cd', u'Hard Disk, CD-ROM'),
    (u'a', u'Floppy Drive'),
    (u'c', u'Hard Disk'),
    (u'd', u'CD-ROM'),
    (u'n', u'Network'),
]

HVM_DISK_TYPES = [
    (u'ioemu', u'ioemu'),
]

# HV Choices
HV_DISK_TEMPLATES = [
    (u'plain', u'Plain'),
    (u'drbd', u'DRBD'),
    (u'file', u'File'),
    (u'diskless', u'Diskless')
]

# HV Choices
HV_DISK_TEMPLATES_SINGLE_NODE = [
    (u'plain', u'plain'),
    (u'file', u'file'),
    (u'diskless', u'diskless')
]

HV_DISK_TYPES = [
    (u'paravirtual',u'Paravirtual'),
    (u'ide',u'IDE'),
]

HV_NIC_MODES = [
    (u'routed', u'Routed'),
    (u'bridged', u'Bridged')
]

HV_NIC_TYPES = [
    (u'e1000',u'e1000'),
    (u'rtl8139',u'RTL8139'),
    (u'ne2k_isa',u'NE2000 (ISA)'),
    (u'ne2k_pci',u'NE2000 (PCI)'),
    (u'paravirtual',u'Paravirtual'),
]

HV_BOOT_ORDER = KVM_BOOT_ORDER

HV_DISK_CACHES = [
    (u'none',u'None'),
    (u'default',u'Default'),
    (u'writethrough',u'Writethrough'),
    (u'writeback',u'Writeback'),
]

HV_SECURITY_MODELS = [
    (u'none',u'None'),
    (u'user',u'User'),
    (u'pool',u'Pool'),
]

HV_USB_MICE = [
    (u'mouse',u'Mouse'),
    (u'tablet',u'Tablet'),
]

ALL_DISK_TYPES = HV_DISK_TYPES + KVM_DISK_TYPES + HVM_DISK_TYPES
ALL_NIC_TYPES = HV_NIC_TYPES + KVM_NIC_TYPES
ALL_BOOT_ORDER = KVM_BOOT_ORDER + HVM_BOOT_ORDER

KVM_CHOICES = {
    'disk_type': HV_DISK_TYPES + KVM_DISK_TYPES,
    'nic_type': HV_NIC_TYPES + KVM_NIC_TYPES,
    'boot_order': KVM_BOOT_ORDER,
}

HVM_CHOICES = {
    'disk_type': HV_DISK_TYPES + HVM_DISK_TYPES,
    'nic_type': HV_NIC_TYPES,
    'boot_order': HVM_BOOT_ORDER,
}

ALL_CHOICES = {
    'disk_type': ALL_DISK_TYPES,
    'nic_type': ALL_NIC_TYPES,
    'boot_order': ALL_BOOT_ORDER,
}

NO_CHOICES = {
    'disk_type': None,
    'nic_type': None,
    'boot_order': None,
}
