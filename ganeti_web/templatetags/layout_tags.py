from django.conf import settings
from django import template
from django.template.base import NodeList

register = template.Library()

OPEN_REG = getattr(settings, 'ALLOW_OPEN_REGISTRATION', True)


@register.tag
def open_registration(parser, token):
    nodelist_true = parser.parse(('else', 'endopen_registration'))
    token = parser.next_token()

    if token.contents == 'else':
        nodelist_false = parser.parse(('endopen_registration',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()

    return OpenRegistrationNode(OPEN_REG, nodelist_true, nodelist_false)


class OpenRegistrationNode(template.Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, var, nodelist_true, nodelist_false):
        self.var = var
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        if OPEN_REG:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)
