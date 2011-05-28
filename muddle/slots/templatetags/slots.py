from django import template
from django.template import Node, NodeList, TemplateSyntaxError

register = template.Library()

from muddle.slots.registration import MUDDLE_SLOTS


@register.tag
def slot(parser, token):
    """ renders a slot """
    bits = token.contents.split()
    if len(bits) != 2:
            raise TemplateSyntaxError, "'slot' tag takes one argument: the slot key to be included"
    key = str(bits[1])

    inner_nodelist = parser.parse(('endslot',))
    parser.delete_first_token()

    try:
        slot = MUDDLE_SLOTS[str(key)]
    except KeyError:
        # no slats registered for this slot
        slot = None

    return SlotNode(slot, inner_nodelist)


class SlotNode(Node):

    def __init__(self, slot=None, nodelist=None):
        if slot and slot.template_slats:
            if nodelist:
                self.slats = slot.template_slats
                self.render = self.render_slats
                self.inner_nodelist = nodelist

            else:
                # XXX when there's no inner nodes just monkey patch template
                # render method to reduce traversal to nodelist
                nodes = [SlatNode(slat) for slat in slot.template_slats]
                self.render = NodeList(nodes).render
    
    def render(self, context):
        return NodeList().render(context)

    def render_slats(self, context):
        nodelist = NodeList()
        inner_nodelist = self.inner_nodelist
        
        context.push()
        for slat in self.slats:
            context['slat'] = slat.template.render(context)
            nodelist.append(inner_nodelist.render(context))
        context.pop()

        return nodelist.render(context)
        


class SlatNode(Node):
    def __init__(self, slat, nodelist=None):
        self.render = slat.template.render
