from django import template
register = template.Library()

from core.models import PluginConfig
from core.plugins.registerable import PERM_NONE
from core.views import manager

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
    try:
        return object_.__getattribute__(key)
    except:
        return None


@register.filter(name='f')
def f(object_, key):
    """
    returns the property of the object
    """
    return object_.__getattribute__(key)()


@register.filter(name='perms')
def perms(instance, user):
    """
    Returns permissions for the instance/user combination
    """
    wrapper = manager['ModelManager'][instance.__class__.__name__]
    return wrapper.has_perms(user.get_profile(), id=instance.id)
    
    
@register.filter(name='has_perm')
def has_perm(perms, mask):
    """
    returns whether or not the perms contain the mask requested
    """
    return perms & mask


@register.filter(name='link')
def link(wrapper):
    global manager
    if 'DetailView:%s' % wrapper.name() in manager['ViewManager']:
        return wrapper.name()
    return None


@register.filter(name='echo')
def echo(x):
    print 'echo: %s' % x
    return True