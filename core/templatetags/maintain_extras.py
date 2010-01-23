from django import template
register = template.Library()

from core.models import PluginConfig

@register.filter(name='config')
def config(class_):
    """
    Fetches config for a plugin class
    """
    return PluginConfig.objects.get(name=class_.__name__)


@register.filter(name='index')
def index(object_, key):
    """
    returns the index of the object_
    """
    return object_[key]
    

@register.filter(name='get')
def get(object_, key):
    """
    returns the property of the object
    """
    return object_.__getattribute__(key)