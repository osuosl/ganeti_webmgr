from django.shortcuts import render
from django.template.context import RequestContext
from muddle.slots.registration import MUDDLE_SLOTS

__all__ = ['muddled_response', 'SlotProcessor']


def muddled_response(key, request, template_name, *args, **kwargs):
    try:
        slats = MUDDLE_SLOTS[key].context_slats
    except KeyError:
        slats = None
    
    if slats:
        # must have a context_instance to add context variables
        if 'context_instance' in kwargs:
            context_instance = kwargs.pop('context_instance')
        else:
            current_app = kwargs.pop('current_app', None)
            context_instance = RequestContext(request, current_app=current_app)

        # execute each slat context processor 
        for slat in slats:
            context_instance.update(slat(request))
    else:
        context_instance = None
    
    return render(request, template_name, context_instance=context_instance, \
                *args, **kwargs)


class SlotProcessor(object):
    """
    SlotProcessor is used with RequestContexts.  It will load and execute all
    context processors and return them as a single dict.
    """

    def __init__(self, key):
        try:
            self.slats = MUDDLE_SLOTS[key].context_slats
        except KeyError:
            self.slats = None
    
    def __call__(self, request):
        data = {}
        if self.slats:
            for slat in self.slats:
                data.update(slat(request))
        return data