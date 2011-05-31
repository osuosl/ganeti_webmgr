from django.conf import settings
from django.template import loader

from muddle.core.apps.plugins import load_app_plugin


__all__ = ['initialize', 'register']

DEFAULT_CATEGORY = getattr(settings, 'DEFAULT_CATEGORY', 'general')

MUDDLE_SLOTS = {}


def initialize():
    """
    Initialize the app settings module
    """
    print 'Loading Muddle Slots'
    load_app_plugin('slats')


def register(key, *slats):
    """
    Register
    """
    global MUDDLE_SLOTS
    try:
        slot = MUDDLE_SLOTS[key]
    except KeyError:
        slot = Slot()
        MUDDLE_SLOTS[key] = slot
    slot.add_slats(slats)


class Slot(object):

    def __init__(self):
        self.context_slats = []
        self.template_slats = []

    def add_slats(self, slats):
        for slat in slats:
            if isinstance(slat, (ContextSlat,)):
                if any((s for s in self.context_slats if s.function is slat.function)):
                    continue
                self.context_slats.append(slat)
            
            elif isinstance(slat, (TemplateSlat,)):
                if any((s for s in self.template_slats if s.origin == slat.origin)):
                    continue
                self.template_slats.append(slat)
            
            else:
                raise RuntimeError('Invalid slat type')


class ContextSlat(object):
    """
    A slat that provides additional context.  This class wraps a handler
    function.  It contains additional functionality that might be included with
    """
    function = None

    def __init__(self, function):
        assert(callable(function))
        self.function = function

    def __call__(self, request):
        return self.function(request)

    def __eq__(self, o):
        if isinstance(o, (ContextSlat,)):
            return o.function == self.function
        return o == self.function


class TemplateSlat(object):
    """
    A slat that provides additional content to a template.  TemplateSlats can
    be inline by just providing a template.  TemplateSlats can optionally be
    loaded using ajax by providing an ajax URL.  When an ajax url is provided
    a special ajax template is used to render html & javascript that handles the
    asynchronous loading via ajax.
    """
    
    def __init__(self, template=None, ajax=None):
        assert(isinstance(template, (str,)))
        self.origin = template
        self.render_template = template
        self.ajax = ajax

        template = "AJAX_TEMPLATE" if self.ajax else self.render_template
        self.template = loader.get_template(template)

    def render(self):
        self.template.render()

    def __repr__(self):
        return self.origin

    def __eq__(self, o):
        if isinstance(o, (TemplateSlat,)):
            return o.origin == self.origin
        return o == self.origin