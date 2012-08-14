from django.shortcuts import render_to_response
from django.template import RequestContext

from muddle import settings_processor, perms_processor
from muddle.plugins.view import View
from muddle.plugins.models.wrapper import ModelWrapper
from muddle.plugins.registerable import *


class ModelListView(View):
    """
    Generic view generated for a model.  For this view to function the model
    must also be registered.
    """
    
    def __init__(self, model):
        self.model = model
        if self.model.__class__ == ModelWrapper:
            self.regex = '^%s$' % self.model.name()
        else:
            self.regex = '^%s$' % self.model.__name__
    
    def __call__(self, request):
        c = RequestContext(request, processors=[settings_processor, \
                                                perms_processor])

        # get permissions on this class of object
        user = request.user.get_profile()
        perms = user.get_permissions(self.model.name())
        if not perms:
            groups = iter(user.groups.all())
            try:
                while not perms:
                    perms = groups.next().get_permissions(self.model.name())
            except StopIteration:
                pass
            
        if not perms:
            return render_to_response('errors/403.html', context_instance=c)
        
        flattened = reduce(lambda x,y: x|y, perms.values())
        instances = []
        for i in self.model.model.objects.all():
            perms = self.model.has_perms(user, id=i.id)
            flattened = flattened | perms
            if perms & PERM_READ:
                instances.append(i)
        
        link_view = 'DetailView:%s' % self.model.name()
        if link_view in self.manager:
            link = self.manager[link_view]
        else:
            link = None
        
        return render_to_response('view/generic_model_list.html', \
            {'instances':instances, 'wrapper':self.model, 'link':link, \
             'perms':perms}
            , context_instance=c)
    
    def _register(self, manager):
        if self.model.__class__ != ModelWrapper:
            self.model = manager.manager['ModelManager'][self.model.__name__]
        self.manager = manager
    
    def name(self):
        if self.model.__class__ == ModelWrapper:
            return 'ListView:%s' % self.model.name()
        return 'ListView:%s' % self.model.__name__


class ModelView(View):
    """
    Generic view for displaying instances of a model.
    """
    
    def __init__(self, model):
        """
        @param model - Model or ModelWrapper
        """
        self.model = model
        
        if self.model.__class__ == ModelWrapper:
            self.regex = '^%s/(\d+)$' % self.model.name()
        else:
            self.regex = '^%s/(\d+)$' % self.model.__name__
    
    def _register(self, manager):
        if self.model.__class__ != ModelWrapper:
            self.model = manager.manager['ModelManager'][self.model.__name__]
    
    def __call__(self, request, id):
        """
        Overridden to process the requests directly rather delegating to another
        function
        """
        user = request.user.get_profile()
        perms = self.model.has_perms(user, id=id)
        try:
            instance = self.model.model.objects.get(id=id)
        except self.model.model.DoesNotExist:
            return render_to_response('errors/404.html')
        
        if perms & PERM_READ != PERM_READ:
            return render_to_response('errors/403.html')
        
        c = RequestContext(request, processors=[settings_processor, \
                                                perms_processor])
        return render_to_response('view/generic_model_view.html',
            {'wrapper': self.model, 'instance':instance, 'perms':perms}
            , context_instance=c)
    
    def name(self):
        if self.model.__class__ == ModelWrapper:
            return 'DetailView:%s' % self.model.name()
        return 'DetailView:%s' % self.model.__name__
