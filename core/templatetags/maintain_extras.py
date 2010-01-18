from django import template
register = template.Library()

from core.models import PluginConfig

@register.filter(name='config')
def config(class_):
    """
    Fetches config for a plugin class
    """
    return PluginConfig.objects.get(name=class_.__name__)
