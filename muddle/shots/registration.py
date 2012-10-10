from django.conf import settings
from django.template import loader

from muddle.core.apps.plugins import load_app_plugin


__all__ = ['initialize', 'register']

DEFAULT_CATEGORY = getattr(settings, 'DEFAULT_CATEGORY', 'general')

MUDDLE_SHOTS = {}


def initialize():
    """
    Initialize the app settings module
    """
    print 'Loading Muddle Shots'
    load_app_plugin('muddle.mixers')


def register(key, *mixers):
    """
    Register
    """
    global MUDDLE_SHOTS
    try:
        shot = MUDDLE_SHOTS[key]
    except KeyError:
        shot = Shot()
        MUDDLE_SHOTS[key] = shot
    shot.add_mixers(mixers)


class Shot(object):

    def __init__(self):
        self.template_mixers = []

    def add_mixers(self, mixers):
        for mixer in mixers:
            if isinstance(mixer, (TemplateMixer,)):
                if any((s for s in self.template_mixers if s.origin == mixer.origin)):
                    continue
                self.template_mixers.append(mixer)
            else:
                raise RuntimeError('Invalid mixer type')


class TemplateMixer(object):
    """
    A mixer that provides additional content to a template.  TemplateMixers can
    be inline by just providing a template.  TemplateMixers can optionally be
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
        if isinstance(o, (TemplateMixer,)):
            return o.origin == self.origin
        return o == self.origin
