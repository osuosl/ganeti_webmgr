from django import template
from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
import re

from ganeti.models import Quota


register = Library()

"""
These filters were taken from Russel Haering's GanetiWeb project
"""

@register.filter
@stringfilter
def render_node_status(status):
    if status:
        return "Offline"
    else:
        return "Online"

@register.filter
@stringfilter
def render_instance_status(status):
    return status.replace('ADMIN_', '', 1)\
                 .replace('ERROR_', '', 1)\
                 .capitalize()

@register.filter
@stringfilter
def render_storage(value):
    amount = float(value)
    if amount >= 1024:
        return "%.2f G" % (amount/1024)
    else:
        return "%d M" % int(amount)

@register.filter
def quota(cluster_user, cluster):
    """
    Returns the quota for user/cluster combination.
    """
    try:
        return Quota.objects.get(user=cluster_user, cluster=cluster)
    except Quota.DoesNotExist:
        return None

@register.simple_tag
def node_memory(node):
    total = float(node['mtotal'])/1024
    free = float(node['mfree'])/1024
    return "%.1f / %.1f" % (free, total)

@register.simple_tag
def node_disk(node):
    total = node['dtotal']/1024
    free = node['dfree']/1024
    return "%d/%d" % (free, total)

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