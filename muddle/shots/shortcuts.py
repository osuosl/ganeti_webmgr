from django.shortcuts import render
from django.template.context import RequestContext
from muddle.shots.registration import MUDDLE_SHOTS

__all__ = ['muddled_response', 'ShotProcessor']


def muddled_response(key, request, template_name, *args, **kwargs):
    try:
        mixers = MUDDLE_SHOTS[key].context_mixers
    except KeyError:
        mixers = None
    
    if mixers:
        # must have a context_instance to add context variables
        if 'context_instance' in kwargs:
            context_instance = kwargs.pop('context_instance')
        else:
            current_app = kwargs.pop('current_app', None)
            context_instance = RequestContext(request, current_app=current_app)

        # execute each mixer context processor
        for mixer in mixers:
            context_instance.update(mixer(request))
    else:
        context_instance = None
    
    return render(request, template_name, context_instance=context_instance, \
                *args, **kwargs)


class ShotProcessor(object):
    """
    ShotProcessor is used with RequestContexts.  It will load and execute all
    context processors and return them as a single dict.
    """

    def __init__(self, key):
        try:
            self.mixers = MUDDLE_SHOTS[key].context_mixers
        except KeyError:
            self.mixers = None
    
    def __call__(self, request):
        data = {}
        if self.mixers:
            for mixer in self.mixers:
                data.update(mixer(request))
        return data