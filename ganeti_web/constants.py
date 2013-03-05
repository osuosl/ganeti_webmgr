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

VERSION = '0.9.1'
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
    (u'diskless', u'Diskless'),
    (u'sharedfile', u'Sharedfile'),
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
    (u'', u''),
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

VM_CREATE_HELP = {
    'owner': """<p>The owner indicates who this virtual machine belongs to. Resources
                used by the virtual machine will be deducted from the owner's
                quota.</p>""",
    'cluster': "<p>Which ganeti cluster to deploy the new virtual machine on.</p>",
    'hostname': """<p>Fully qualified domain name <i>(<b>FQDN</b>)</i> to
                    assign to this virtual machine.<i>(e.g.
                    hostname.example.org)</i></p> <p>Note: It is strongly
                    recommended to leave the DNS Name Check box checked, to
                    confirm that your selected hostname is valid. Spaces and
                    certain special characters are not permitted in the
                    hostname field because they can cause errors with editing
                    or deleting the VM.</p>""",
    'hypervisor': "<p>Which hypervisor the new virtual machine will run under.</p>",
    'start': """<p>Uncheck this if you don't want the instance to automatically
                start after creation. If you do so, you can start it manually
                on the virtual machine detail page.</p> <p>This option is only
                available if you choose to install an operating system when
                creating the virtual machine.</p>""",
    'name_check': """<p>Check the virtual machine DNS name via the resolver
                     <i>(e.g. in DNS or /etc/hosts, depending on your
                     setup)</i>. Since the name check is used to compute the IP
                     address this also enables/disables IP checks <i>(e.g.  if
                     the IP is pingable)</i>.</p> <p>This is useful for setups
                     that deploy virtual machines using dynamic DNS and thus
                     the name is not resolvable yet.</p> """,
    'iallocator': """<p>Automatically select primary and secondary node to
                     allocate disks on.</p> <p>When selected it will use the
                     cluster default <a
                     href="http://docs.ganeti.org/ganeti/current/html/iallocator.html">
                     iallocator</a> (if set by the cluster). The iallocator
                     being used will be displayed after the checkbox.</p> """,
    'disk_template': """<p>Disk layout template for the virtual machine on the
                        cluster node.</p> <p>The available choices are:</p>
                        <ul> <li><b>plain</b> - Disk Devices will be logical
                        volumes <i>(e.g. LVM)</i></li> <li><b>drbd</b>- Disk
                        devices will be <a href="http://www.drbd.org/">DRBD</a>
                        (version 8.x) on top of LVM volumes</li>
                        <li><b>file</b> - Disk devices will be regular files
                        <i>(e.g.  qcow2)</i></li> <li> <b>diskless</b> - This
                        creates a virtual machine with no disks. Its useful for
                        testing only (or other special cases).</li> </ul> <p>
                        If drbd is selected, then a primary and secondary node
                        will need to be chosen unless automatic allocation has
                        been selected as well. DRBD will allow the virtual
                        machine to use live migration and failover in case one
                        of the nodes goes offline.</p>""",
    'pnode': """<p>The primary node to use for the virtual machine (in case
                automatic allocation is not used).</p>""",
    'snode': """<p>The secondary node to use for the virtual machine (in case
                automatic allocation is not used).  </p> <p> This is only
                required when using the drbd disk template.  </p> """,
    'os': """<p>Operating system to install on the virtual machine. Your
             choices are limited to the images configured on the cluster. </p>
             <p> The text in <b>bold</b> signifies the Ganeti Operating System
             Type which may be called debootstrap, image, or some other type.
             The text that is selectable is the operating system (or os-type
             variant) that the cluster has access to.  </p> """,
    'disk_size': """<p> Size of the system disk to allocate to this virtual
                    machine. If no units are given, megabytes is assumed.  </p>
                    <p> Acceptable Formats: </p> <ul> <li> <b>M</b> or MB -
                    (megabytes) </li> <li> <b>G</b> or GB - (gigabytes) </li>
                    <li> <b>T</b> or TB - (terabytes) </li> </ul> <p><b><i>This
                    will be deducted from the owner's quota.</i></b></p>""",
    'disk_type': """<p> This parameter determines the way the disks are
                    presented to the virtual machine. The possible options are:
                    </p> <ul> <li><b>paravirtual</b> - (HVM &amp; KVM)</li>
                    <li> <b>ioemu</b> - (default for HVM &amp; KVM) (HVM &amp;
                    KVM) </li> <li><b>ide</b> - (HVM &amp; KVM)</li>
                    <li><b>scsi</b> - (KVM)</li> <li><b>sd</b> - (KVM)</li>
                    <li><b>mtd</b> - (KVM)</li> <li><b>pflash</b> - (KVM)</li>
                    </ul><p>Valid for the Xen HVM and KVM hypervisors.</p>""",
    'nic_mode': """ <p> This option specifies how the virtual machine connects
                    to the network. More information on this can be found in
                    the <a
                    href="http://docs.ganeti.org/ganeti/current/html/install.html#configuring-the-network">Ganeti
                    tutorial documentation</a>.  </p> <p>When in doubt, choose
                    <b>bridged</b>.</p> <ul> <li> <b>bridged</b> - The virtual
                    machine's network interface will be attached to a software
                    bridge running on the node.  </li> <li><b>routed</b> - The
                    virtual machine's network interface will be routed.  </li>
                    </ul>""",
    'nic_type': """<p> This parameter determines the way the network cards are
                   presented to the virtual machine. The possible options are:
                   </p> <ul> <li><b>rtl8139</b> - (default for Xen HVM) (HVM
                   &amp; KVM)</li> <li><b>ne2k_isa</b> - (HVM &amp; KVM)</li>
                   <li><b>ne2k_pci</b> - (HVM &amp; KVM)</li>
                   <li><b>i82551</b> - (KVM)</li> <li><b>i82557b</b> -
                   (KVM)</li> <li><b>i82559er</b> - (KVM)</li>
                   <li><b>pcnet</b> - (KVM)</li> <li><b>e1000</b> - (HVM &amp;
                   KVM)</li> <li><b>paravirtual</b> - (default for KVM) (KVM
                   &amp; HVM)</li> </ul> <p>Valid for the Xen HVM and KVM
                   hypervisors.</p> """,
    'kernel_path': """<p> This option specifies the path (on the node) to the
                      kernel to boot the virtual machine with. Xen PVM
                      instances always require this, while for KVM if this
                      option is empty, it will cause the machine to load the
                      kernel from its disks.  </p> <p>Valid for the Xen PVM
                      and KVM hypervisors.</p> """,
    'root_path': """<p> This option specifies the name of the root device.
                    This is always needed for Xen PVM, while for KVM it is only
                    used if the kernel_path option is also specified.  </p>
                    <p>Valid for the Xen PVM and KVM hypervisors.</p> """,
    'serial_console': """<p> This boolean option specifies whether to emulate
                         a serial console for the instance.  </p> <p>Valid for
                         the KVM hypervisor.</p> """,
    'boot_order': """<p>Value denoting boot order for the virtual machine.</p>
                     <ul> <li><b>Hard Disk</b> - boot from the first disk
                     device</li> <li> <b>CD-ROM</b> - boot from the cdrom
                     (requires CD Image path being set) </li>
                     <li><b>Network</b>
                     - boot from the network (such as PXE)</li> </ul> <p>Valid
                       for the Xen HVM and KVM hypervisors.</p> """,
    'cdrom_image_path': """<p> The path to a CDROM image on the node to attach
                           to the virtual machine.  </p> <p>Valid for the Xen
                           HVM and KVM hypervisors.</p> """,
    'cdrom2_image_path': """<p> The path to the second CDROM image, if
                            multiple CDROMs are supported by the selected
                            hypervisor. </p> """,
    'no_install': """<p>Skip installing the operating system when creating
                     the VM. Use this option if you plan to manually set up the
                     virtual machine.  </p> <p> Note that even if you aren't
                     installing an operating system, you must select one from
                     the list to fulfill Ganeti's parameter requirements.  The
                     selected OS will be associated with the VM, but not
                     installed.  </p> """,
    'choices': """<p>Template - A re-usable Virtual Machine Template. Check
                     this box if you want to save the options for easy re-use
                     later.</p> <p>Virtual Machine - Start up an instance with
                     the options chosen in this Wizard""",
}

VM_HELP = {
    'vcpus': """<p>Number of virtual cpus to allocate to this virtual
                machine.</p> <p><b><i>This will be deducted from the owner's
                quota.</i></b></p> """,
    'memory': """<p> Amount of ram to allocate to this virtual machine. If no
                 units are given, megabytes is assumed.  </p> <p><b><i>This will
                 be deducted from the owner's quota.</i></b></p> """,
    'nic_link': """<p>In <b>bridged</b> mode, it specifies the bridge
                   interface to attach this NIC to on the node <i>(e.g.
                   br0)</i>.  </p> <p>In <b>routed</b> mode it's intended to
                   differentiate between different routing tables/virtual
                   machine groups (but the meaning is dependant on the network
                   script, see <a
                   href="http://docs.ganeti.org/ganeti/current/man/gnt-cluster.html">
                   gnt-cluster(8)</a> for more details.  </p> """,
    'nic_mac': """<p> This option specifies a MAC address to be associated
                  with the NIC.  </p> <p> Any valid MAC address may be used.
                  </p>""",
    'template_name': """<p> The name of this template. Templates will be
                        sorted by template name when they appear in a list.
                        </p> """,
    'description': "<p>Optional. A short description of the template.</p>",
}

VM_RENAME_HELP = {
    'hostname': """<p>Domain name or host name to assign to this virtual machine;
                   e.g. <tt>example.org</tt> or
                   <tt>subdomain.example.org</tt>.</p>""",
    'ip_check': "<p>Whether to ensure instance's IP address is inactive.</p>",
    'name_check': """<p> Check the virtual machine DNS name via the resolver <i>(e.g. in DNS or
                     /etc/hosts, depending on your setup)</i>. Since the name
                     check is used to compute the IP address this also
                     enables/disables IP checks <i>(e.g.  if the IP is
                     pingable)</i>.  </p> <p> This is useful for setups that
                     deploy virtual machines using dynamic DNS and thus the
                     name is not resolvable yet.  </p> <p> <b>Use with
                     caution!</b> If left unchecked you may run into name/ip
                     collisions. </p>""",
}

