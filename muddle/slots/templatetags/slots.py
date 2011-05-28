from django import template
from django.template import Node, NodeList, TemplateSyntaxError

register = template.Library()

from muddle.slots.registration import MUDDLE_SLOTS


@register.tag
def slot(parse, token):
    """ renders a slot """
    bits = token.contents.split()
    if len(bits) != 2:
            raise TemplateSyntaxError, "'slot' tag takes one argument: the slot key to be included"
    key = str(bits[1])

    try:
        slot = MUDDLE_SLOTS[str(key)]
    except KeyError:
        # no slats registered for this slot
        slot = None

    return SlotNode(slot)


class SlotNode(Node):

    def __init__(self, slot=None):
        if slot and slot.template_slats:
            nodes = [SlatNode(slat) for slat in slot.template_slats]
            self.render = NodeList(nodes).render

    def render(self, context):
        return NodeList().render(context)


class SlatNode(Node):
    def __init__(self, slat):
        self.render = slat.template.render