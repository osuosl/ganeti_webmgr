from copy import copy
from django import template
register = template.Library()

from muddle.shots.tests import context as global_context


@register.simple_tag(takes_context=True)
def context_dump(context):
    """ a simple tag used in testing that allows us to grab the context """
    global_context.CONTEXT = copy(context)