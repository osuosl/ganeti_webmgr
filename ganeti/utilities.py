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


def cluster_default_info(cluster):
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
    hv = info['default_hypervisor']
    hvparams = info['hvparams'][hv]

    try:
        iallocator_info = info['default_iallocator']
    except:
        iallocator_info = None

    return {
        'iallocator': iallocator_info,
        'hypervisor':hv,
        'vcpus':beparams['vcpus'],
        'memory':beparams['memory'],
        'disk_type':hvparams['disk_type'],
        'nic_type':hvparams['nic_type'],
        'nic_mode':info['nicparams']['default']['mode'],
        'nic_link':info['nicparams']['default']['link'],
        'kernel_path':hvparams['kernel_path'],
        'root_path':hvparams['root_path'],
        'serial_console':hvparams['serial_console'],
        'boot_order':hvparams['boot_order'],
        'cdrom_image_path':hvparams['cdrom_image_path'],
        }


def cluster_os_list(cluster):
    """
    Create a detailed manifest of available operating systems on the cluster.
    """

    return os_prettify(cluster.rapi.GetOperatingSystems())


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
