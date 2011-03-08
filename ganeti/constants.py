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
    ('', '-------------'),
    ('master-candidate','Master Candidate'),
    ('regular','Regular'),
    ('drained','Drained'),
    ('offline','Offline'),
)
ROLE_MAP = {
    'C':'master-candidate',
    'R':'regular',
    'D':'drained',
    'O':'offline',
}
# KVM Choices
KVM_DISK_TEMPLATES = [
    (u'', u'---------'),
    (u'plain', u'plain'),
    (u'drbd', u'drbd'),
    (u'file', u'file'),
    (u'diskless', u'diskless')
]
KVM_DISK_TYPES = [
    (u'', u'---------'),
    (u'paravirtual',u'paravirtual'),
    (u'ide',u'ide'),
    (u'scsi',u'scsi'),
    (u'sd',u'sd'),
    (u'mtd',u'mtd'),
    (u'pflash',u'pflash'),
]
KVM_NIC_MODES = [
    (u'', u'---------'),
    (u'routed', u'routed'),
    (u'bridged', u'bridged')
]
KVM_NIC_TYPES = [
    (u'', u'---------'),
    (u'rtl8139',u'rtl8139'),
    (u'ne2k_isa',u'ne2k_isa'),
    (u'ne2k_pci',u'ne2k_pci'),
    (u'i82551',u'i82551'),
    (u'i82557b',u'i82557b'),
    (u'i82559er',u'i82559er'),
    (u'pcnet',u'pcnet'),
    (u'e1000',u'e1000'),
    (u'paravirtual',u'paravirtual'),
]
KVM_BOOT_ORDER = [
    ('disk', 'Hard Disk'),
    ('cdrom', 'CD-ROM'),
    ('network', 'Network'),
]
KVM_DISK_CACHES = [
    (u'default',u'Default'),
    (u'writethrough',u'Writethrough'),
    (u'writeback',u'Writeback'),
]
KVM_SECURITY_MODELS = [
    (u'none',u'None'),
    (u'user',u'User'),
    (u'pool',u'Pool'),
]
KVM_FLAGS = [
    (u'', u'---------'),
    (u'enabled', u'Enabled'),
    (u'disabled', u'Disabled'),
]
KVM_USB_MICE = [
    (u'', u'---------'),
    (u'mouse',u'Mouse'),
    (u'tablet',u'Tablet'),
]
# Xen HVM Choices
