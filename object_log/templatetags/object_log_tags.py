from django.template import Library
from django.utils.safestring import SafeString

register = Library()

@register.filter()
def render_context(log_item, context):
    """
    helper tag needed for adding extra context when rendering a LogItem
    """
    return SafeString(log_item.render(**context))