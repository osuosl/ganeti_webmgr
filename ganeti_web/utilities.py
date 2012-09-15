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
from collections import defaultdict
from ganeti_web import constants
from ganeti_web.caps import req_maxmem

from ganeti_web.util.client import GanetiApiError


def cluster_default_info(cluster, hypervisor=None):
    """
    Returns a dictionary containing the following
    default values set on a cluster:
        iallocator, hypervisors, vcpus, ram, nictype,
        nicmode, kernelpath, rootpath, serialconsole,
        bootorder, imagepath
    """
    # Create variables so that dictionary lookups are not so horrendous.
    info = cluster.info
    beparams = info['beparams']['default']
    hvs = info['enabled_hypervisors']

    if hypervisor is not None:
        if hypervisor not in hvs:
            raise RuntimeError("Was asked to deal with a cluster/HV mismatch")
        else:
            hv = hypervisor
    else:
        hv = info['default_hypervisor']

    hvparams = info['hvparams'][hv]
    if hv == 'kvm':
        c = constants.KVM_CHOICES
    elif hv == 'xen-hvm' or hv == 'xen-pvm':
        c = constants.HVM_CHOICES
        if hv == 'xen-pvm':
            # PVM does not have disk types or nic types, so these options get
            # taken from HVM. This does not affect forms as pvm ignores
            # the disk_type and nic_type fields.
            hvparams['disk_type'] = info['hvparams']['xen-hvm']['disk_type']
            hvparams['nic_type'] = info['hvparams']['xen-hvm']['nic_type']
    else:
        c = constants.NO_CHOICES

    disktypes = c['disk_type']
    nictypes = c['nic_type']
    bootdevices = c['boot_order']

    try:
        iallocator_info = info['default_iallocator']
    except:
        iallocator_info = None

    if 'nicparams' in info:
        nic_mode = info['nicparams']['default']['mode']
        nic_link = info['nicparams']['default']['link']
    else:
        nic_mode = None
        nic_link = None

    extraparams = {
        'boot_devices': bootdevices,
        'disk_types': disktypes,
        'hypervisor': hv,
        'hypervisors': zip(hvs, hvs),
        'iallocator': iallocator_info,
        'nic_types': nictypes,
        'nic_mode': nic_mode,
        'nic_link': nic_link,
        'vcpus': beparams['vcpus'],
        }

    if req_maxmem(cluster):
        extraparams['memory'] = beparams['maxmem']
    else:
        extraparams['memory'] = beparams['memory']

    return dict(hvparams, **extraparams)


def hv_prettify(hv):
    """
    Prettify a hypervisor name, if we know about it.
    """

    prettified = {
        "kvm": "KVM",
        "lxc": "Linux Containers (LXC)",
        "xen-hvm": "Xen (HVM)",
        "xen-pvm": "Xen (PVM)",
    }

    return prettified.get(hv, hv)


def cluster_os_list(cluster):
    """
    Create a detailed manifest of available operating systems on the cluster.
    """
    try:
        return os_prettify(cluster.rapi.GetOperatingSystems())
    except GanetiApiError:
        return []


def os_prettify(oses):
    """
    Pretty-print and format a list of operating systems.

    The actual format is a list of tuples of tuples. The first entry in the
    outer tuple is a label, and then each successive entry is a tuple of the
    actual Ganeti OS name, and a prettified display name. For example:

    [
        ("Image",
            ("image+obonto-hungry-hydralisk", "Obonto Hungry Hydralisk"),
            ("image+fodoro-core", "Fodoro Core"),
        ),
        ("Dobootstrop",
            ("dobootstrop+dobion-lotso", "Dobion Lotso"),
        ),
    ]
    """

    # In order to convince Django to make optgroups, we need to nest our
    # iterables two-deep. (("header", ("value, "label"), ("value", "label")))
    # http://docs.djangoproject.com/en/dev/ref/models/fields/#choices
    # We do this by making a dict of lists.
    d = defaultdict(list)

    for name in oses:
        try:
            # Split into type and flavor.
            t, flavor = name.split("+", 1)
            # Prettify flavors. "this-boring-string" becomes "This Boring String"
            flavor = " ".join(word.capitalize() for word in flavor.split("-"))
            d[t.capitalize()].append((name, flavor))
        except ValueError:
            d["Unknown"].append((name, name))

    l = d.items()
    l.sort()

    return l


def compare(x, y):
    """
    Using the python cmp function, returns a string detailing the change in
        difference
    """
    i = cmp(x,y)
    if y is None and i != 0:
        return "removed"
    if isinstance(x, basestring) and i != 0:
        if x == "":
            return "set to %s" % (y)
        elif y == "":
            return "removed"
        return "changed from %s to %s" % (x, y)
    elif isinstance(x, bool) and i != 0:
        if y:
            return "enabled"
        else:
            return "disabled"
    if i == -1:
        return "increased from %s to %s" % (x, y)
    elif i == 1:
        return "decreased from %s to %s" % (x, y)
    else:
        return ""


def contains(e, t):
    """
    Determine whether or not the element e is contained within the list of tuples t
    """
    return any(e == v[0] for v in t)


def get_hypervisor(vm):
    """
    Given a VirtualMachine object, return its hypervisor depending on what hvparam fields
    it contains.
    """
    if vm.info:
        info = vm.info['hvparams']
        if 'serial_console' in info:
            return 'kvm'
        elif 'initrd_path' in info:
            return 'xen-pvm'
        elif 'acpi' in info:
            return 'xen-hvm'
    return None
