# -*- coding: utf-8 -*- vim:encoding=utf-8:

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
from datetime import datetime

import re
from django.contrib.sites.models import Site

from django.db.models import Count
from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import stringfilter,filesizeformat
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ganeti_web.constants import NODE_ROLE_MAP
from ganeti_web.models import Cluster

register = Library()

"""
These filters were created specifically
for the Ganeti Web Manager project
"""
@register.inclusion_tag('ganeti/virtual_machine/vmfield.html')
def vmfield(field):
    return {'field':field}


@register.inclusion_tag('ganeti/virtual_machine/vmfield_disk.html')
def vmfield_disk(form, index):
    return {'field':form['disk_size_%s' % index], 'index':index}


@register.inclusion_tag('ganeti/virtual_machine/vmfield_nic.html')
def vmfield_nic(form, index):
    """
    Render a set of form fields for creating or editing a network card
    """
    data = {'link':form['nic_link_%s' % index],'index':index}
    if 'nic_mode_%s' % index in form.fields:
        data['mode'] = form['nic_mode_%s' % index]
    if 'nic_mac_%s' % index in form.fields:
        data['mac'] = form['nic_mac_%s' % index]
    return data


@register.filter
def class_name(obj):
    """ returns the modelname of the objects class """
    return obj.__class__.__name__


@register.filter
def index(obj, index):
    """ returns index of given object """
    if obj:
        return obj[index]


@register.filter
@stringfilter
def truncate(value, count):
    """
    Truncates a string to be a certain length.

    If the string is shorter than the specified length, it will returned
    as-is.
    """

    if len(value) > count:
        return value[:count - 1] + u"…"

    return value


@register.filter
def timestamp(int):
    """ converts a timestamp to a date """
    return datetime.fromtimestamp(int)


@register.filter
@stringfilter
def ssh_comment(value):
    """
    If value is good SSH public key, then returns the user@hostname for who
    the key is set.
    """
    pos1 = value.find(" ")
    pos2 = value[(pos1+1):].find(" ")
    if pos2 > -1:
        return value[pos1+pos2+2:]
    return value


@register.filter
@stringfilter
def ssh_keytype(value):
    """
    If value is good SSH public key, then returns the user@hostname for who
    the key is set.
    """
    pos = value.find(" ")
    if pos > -1:
        return value[:pos]
    return value


@register.filter
@stringfilter
def ssh_keypart_truncate(value, count):
    try:
        pos0 = value.find(" ")
        pos1 = value[(pos0+1):].find(" ") + pos0
        if (pos0==-1 or pos1==-1) or (pos0==pos1):
            raise BaseException
        value = value[pos0+1:pos1+1]

        if len(value) > count:
            value = "%s ... %s" % (value[:(count/2)], value[(-count/2):])
    except BaseException:
        pass
    finally:
        return value


@register.filter
def is_drbd(vm):
    """ simple filter for returning true of false if a virtual machine
    has DRBD for disklayout
    """
    return 'drbd' == vm.info['disk_template']

@register.filter
def is_shared(vm):
    """ Simple filter for returning true or false if a virtual machine
    has shared for disklayout
    """
    return 'shared' == vm.info['disk_template']

@register.filter
def checkmark(bool):
    """ converts a boolean into a checkmark if it is true """
    if bool:
        str_  = '<div class="check icon"></div>'
    else:
        str_ = '<div class="xmark icon"></div>'
    return mark_safe(str_)


@register.filter
@stringfilter
def node_role(code):
    """ renders full role name from role code """
    return NODE_ROLE_MAP[str(code)]


@register.simple_tag
def current_domain():
    """ returns the domain of the current Site """
    return Site.objects.get_current().domain


@register.filter
def job_fields(info):
    """
    returns tuples of field:value for every field in the job excluding the
    OP_ID

    @param info: dictionary containing op info for this sub-op
    """
    fields = info.copy()
    del fields['OP_ID']

    # repackage job specific dictionaries if present
    hvparams = fields.get('hvparams')
    beparams = fields.get('beparams')
    osparams = fields.get('osparams')

    if hvparams is not None:
        fields.update(hvparams)
    if beparams is not None:
        fields.update(beparams)
    if osparams is not None:
        fields.update(osparams)

    # repackage disks
    if 'disks' in fields:
        for i, disk in enumerate(fields.pop('disks')):
            fields['disk/%s' % i] = disk['size']

    return fields.items()


"""
These filters were taken from Russel Haering's GanetiWeb project
"""

@register.filter
@stringfilter
def render_node_status(status):
    if status:
        return _("Offline")
    else:
        return _("Online")


@register.filter
@stringfilter
def render_instance_status(status):
    return status.replace('ADMIN_', '', 1)\
                 .replace('ERROR_', '', 1)\
                 .capitalize()


@register.filter
@stringfilter
def render_storage(value):
    """
    Render an amount of storage.

    The value should be in mibibytes.
    """
    try:
        amount = float(value)
    except ValueError:
        return "---"

    if amount == 0:
        return "---"

    if amount >= 1024:
        amount /= 1024

        if amount >= 1024:
            amount /= 1024
            return "%.4f TiB" % amount

        return "%.2f GiB" % amount
    else:
        return "%d MiB" % amount


@register.filter
def quota(cluster_user, cluster):
    """
    Returns the quota for user/cluster combination.
    """
    return cluster.get_quota(cluster_user)


@register.filter
def cluster_admin(user):
    """
    Returns whether the user has admin permission on any Cluster
    """
    return user.has_any_perms(Cluster, ['admin'])


@register.filter
def format_job_op(op):
    return op[3:].replace("_", " ").title()


@register.filter
def format_job_log(log):
    """ formats a ganeti job log for display on an html page """
    formatted = log.replace('\n','<br/>')
    return mark_safe(formatted)

@register.simple_tag
def format_part_total(part, total):
    """
    Pretty-print a quantity out of a given total.
    """
    if total <= 0 or part < 0:
        return _("unknown")

    try:
        part = float(part) / 1024
        total = float(total) / 1024
    except ValueError:
        return _("unknown")

    for i, num in enumerate((part, total)):
        num = "%.2f" % num
        if "." in num:
            num = num.rstrip("0").rstrip(".")
        if i == 0:
            part = num
        elif i == 1:
            total = num

    return "%s / %s" % (part, total)


@register.simple_tag
def diff(a, b):
    if a and b:
        return int(a)-int(b)
    else:
        return 0


@register.simple_tag
def diff_render_storage(a, b):
    data = 0
    if a and b:
        data = int(a)-int(b)
    return render_storage(data)


@register.simple_tag
def node_memory(node, allocated=True):
    """
    Pretty-print a memory quantity, in GiB, with significant figures.
    """
    d = node.ram
    if allocated:
        return format_part_total(d['allocated'], d['total'])
    return format_part_total(d['used'], d['total'])


@register.simple_tag
def node_disk(node, allocated=True):
    """
    Pretty-print a disk quantity, in GiB, with significant figures.
    """
    d = node.disk
    if allocated:
        return format_part_total(d['allocated'], d['total'])
    return format_part_total(d['used'], d['total'])


@register.simple_tag
def num_reducer(num1,num2,size_tag):
	"""
	Formats number percentages for progress bars takes in bytes
	"""

	if size_tag == "bytes":
		return "%.2f / %.2f" % (num1,num2)
	elif size_tag == "KB":
		return "%.2f / %.2f" % (num1/1024,num2/1024)
	elif size_tag == "MB":
		return "%.2f / %.2f" % (num1/1024**2,num2/1024**2)
	elif size_tag == "GB":
		return "%.2f / %.2f" % (num1/1024**3,num2/1024**3)
	elif size_tag == "TB":
		return "%.2f / %.2f" % (num1/1024**4,num2/1024**4)
	elif size_tag == "PB":
		return "%.2f / %.2f" % (num1/1024**5,num2/1024**5)


@register.simple_tag
def cluster_memory(cluster, allocated=True,tag=False):
    """
    Pretty-print a memory quantity of the whole cluster in a dynamic unit based on filesizeformat
    """
    d = cluster.available_ram
    size_tag = (filesizeformat(d["total"]*1024**2)).split(" ")[1]
    if tag == True:
	return "[%s]" % size_tag
    if allocated:
        return num_reducer(float(d['allocated']*1024**2), float(d['total']*1024**2),size_tag.strip())
    return num_reducer(float(d['used']*1024**2), float(d['total']*1024**2),size_tag.strip())


@register.simple_tag
def cluster_disk(cluster, allocated=True,tag=False):
    """
    Pretty-print a memory quantity of the whole cluster in a dyanmic unit based on filesizeformat
    """
    d = cluster.available_disk
    size_tag = (filesizeformat(d["total"]*1024**2)).split(" ")[1]
    if tag == True:
	return "[%s]" % (size_tag)
    if allocated:
	return num_reducer(float(d['allocated']*1024**2),float(d['total']*1024**2),size_tag.strip())
    return num_reducer(float(d['used']*1024**2),float(d['total']*1024**2),size_tag.strip())


@register.simple_tag
def format_running_vms(cluster):
    """
    Return number of VMs that are available and number of all VMs
    """
    return "%d/%d" % (cluster.virtual_machines.filter(status="running").count(),
                      cluster.virtual_machines.all().count())


@register.simple_tag
def format_online_nodes(cluster):
    """
    Return number of nodes that are online and number of all nodes
    """
    annotation = cluster.nodes.values('offline').annotate(count=Count('pk'))
    offline = online = 0
    for values in annotation:
        if values['offline']:
            offline = values['count']
        else:
            online = values['count']
    return "%d/%d" % (online, offline+online)


@register.tag
def get_nics(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(\w+) as (\w+)', arg)
    if not m:
        raise TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    instance_name, res_name = m.groups()
    return NicsNode(instance_name, res_name)


class NicsNode(Node):
    def __init__(self, instance_name, res_name):
        self.instance_name = instance_name
        self.res_name = res_name

    def render(self, context):
        instance = context[self.instance_name]
        context[self.res_name] = zip(instance['nic.bridges'], instance['nic.ips'], instance['nic.links'],
                                     instance['nic.macs'], instance['nic.modes'])
        return ''


@register.tag
def get_by_name(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'\s*(.+)\s+"(.+)"\s+as\s+(\w+)', arg)
    if not m:
        raise TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    item_name, attr_name, res_name = m.groups()
    return GetterNode(item_name, attr_name, res_name)


class GetterNode(Node):
    def __init__(self, item_name, attr_name, res_name):
        self.item_name = item_name
        self.attr_name = attr_name
        self.res_name = res_name

    def render(self, context):
        context[self.res_name] = context[self.item_name][self.attr_name]
        return ''

# These filters were created by Corbin Simpson IN THE NAME OF AWESOME!
# Just kidding. Created for ganeti-webmgr at Oregon State University.

@register.filter
@stringfilter
def abbreviate_fqdn(value):
    return value.split(".")[0]


@register.filter
@stringfilter
def render_os(os):
    try:
        t, flavor = os.split("+", 1)
        flavor = " ".join(i.capitalize() for i in flavor.split("-"))
        return mark_safe("%s (<em>%s</em>)" % (flavor, t))
    except ValueError:
        return mark_safe(_("<em>Unknown or invalid OS</em>"))


@register.filter
def mult(value, arg):
    # pinched from http://code.djangoproject.com/ticket/361
    return int(value) * int(arg)
