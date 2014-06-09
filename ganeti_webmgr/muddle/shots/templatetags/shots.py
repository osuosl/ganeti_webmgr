from django import template
from django.template import Node, NodeList, TemplateSyntaxError

register = template.Library()

from ganeti_webmgr.muddle.shots.registration import MUDDLE_SHOTS


@register.tag
def shot(parser, token):
    """ renders a shot """
    bits = token.contents.split()
    if len(bits) != 2:
            raise TemplateSyntaxError(
                "'shot' tag takes one argument: the shot key to be included")
    key = str(bits[1])

    inner_nodelist = parser.parse(('endshot',))
    parser.delete_first_token()

    try:
        shot = MUDDLE_SHOTS[str(key)]
    except KeyError:
        # no mixers registered for this shot
        shot = None

    return ShotNode(shot, inner_nodelist)


class ShotNode(Node):

    def __init__(self, shot=None, nodelist=None):
        if shot and shot.template_mixers:
            if nodelist:
                self.mixers = shot.template_mixers
                self.render = self.render_mixers
                self.inner_nodelist = nodelist

            else:
                # XXX when there's no inner nodes just monkey patch template
                # render method to reduce traversal time
                nodes = [MixerNode(mixer) for mixer in shot.template_mixers]
                self.render = NodeList(nodes).render

    def render(self, context):
        return NodeList().render(context)

    def render_mixers(self, context):
        nodelist = NodeList()
        inner_nodelist = self.inner_nodelist

        context.push()
        for mixer in self.mixers:
            context['mixer'] = mixer.template.render(context)
            nodelist.append(inner_nodelist.render(context))
        context.pop()

        return nodelist.render(context)


class MixerNode(Node):
    def __init__(self, mixer, nodelist=None):
        self.render = mixer.template.render
