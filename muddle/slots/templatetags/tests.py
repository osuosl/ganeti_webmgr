from django import template
register = template.Library()


CONTEXT = None

@register.simple_tag(takes_context=True)
def context_dump(context):
    """ a simple tag used in testing that allows us to grab the context """
    CONTEXT = context