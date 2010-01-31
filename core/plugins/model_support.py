from django.db.models.base import ModelBase
from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, \
                                        SingleRelatedObjectDescriptor, \
                                        ForeignKey, OneToOneField, \
                                        ReverseSingleRelatedObjectDescriptor
from core.plugins.managers.type_manager import ObjectType, TypeManager
from core.plugins.plugin import Plugin
from core.plugins.plugin_manager import PluginManager
from core.plugins.registerable import *
from core.plugins.view import View



class ModelWrapper(Registerable):
    """
    Wrapper around a django model that stores information used to display it.
    Much of this information is already stored internally to the the model. This
    class provides more convenient and stable api to access it.  This shields
    users of this framework from changes within the django internals.
    
    Fields are cached based on their relationship to the wrapped model:
      * fields - model fields
      * one_to_many - wrappers for 1:M and M:N relationships
      * one_to_one - wrappers for 1:1 relationships
      * children - wrappers for models that extend this model   
    """
    target = 'ModelManager'
    _target = ('ModelManager')
    permissions = PERM_ALL
    
    def __init__(self, class_):
        """
        @param class_ - model class this is wrapping.
        @param manager - Root manager enabling this wrapper.
        """
        self.model = class_
        self.fields = []
        self.one_to_many = {}
        self.many_to_one = {}
        self.one_to_one = {}
        self.children = {}
        self.parent = {}

    def _deregister(self, manager):
        """
        Remove relations from all related objects
        """
        for wrapper in self.one_to_one.values():
            wrapper.deregister_related(self.name)
        for key in self.one_to_many.values():
            wrapper.deregister_related(self.name)

    def deregister_related(self, name):
        """
        deregister a related object.  used by other wrappers to update this
        side of the relationship when they are disabled
        """
        field = self.model.__dict__[name]
        if isinstance(field, (ForeignRelatedObjectsDescriptor, )):
            dict_ = self.one_to_many
        elif isinstance(field, (SingleRelatedObjectDescriptor,)):
            dict_ = self.one_to_one
        del dict_[name]


    def _has_perms(self, owner, mask=None, possess=PERM_NONE, id=None):
        """
        Perform a search for permissions.  An owner may have permissions from 
        
        Permissions are stored as a set of binary
        values with each bit representing a permission.  This function performs
        binary operations to compare the set of possible permissions and granted
        permissions for an object.
        
        @param owner - Permissable to check permissions on
        @param model - model to get permissions on
        @param possess - permissions already possessed by the owner
        @param mask - permissions mask to check for.  If None search for all
                    perms
        """
        perms = owner.get_object_permissions(model).items()
        keys = perms.keys()
        possible = mask if mask else wrapper.permissions
        # iterate while there are keys !possessed and permissions left to check
        while not possible & possess and perms:
            path, perm = perms.pop()
            if not possess ^ perm:
                # permission in perm that is not in possess, check it
                if perm[-1] in ('User','Group'):
                    clause = {'__'.join(perm[0]):None}
                elif len(perm) == 1:
                    possess = possess | perm
                    continue
                else:
                    clause = {'%s__in' % '__'.join(perm[0]):owner}
                if model.objects.filter(**clause).filter(id=id).count() == 1:
                    possess = possess | perm
        return possess

    def name(self):
        return self.model.__name__

    def _register(self, manager):
        """
        introspects into the model class finding local and related fields.  This
        information is used to build a composite view of a model and its direct
        relations
        
        All relations are circular and registered with both models. Both ends of
        the relationship being filled out only when the 2nd model is registered.
        This allows the models to be registered in any order without having
        dependency errors.
        """
        # local fields
        for field in self.model._meta.local_fields:

            if isinstance(field, (AutoField,)):
                continue
            elif isinstance(field, (ForeignKey,)):
                related = field.name
                if related in manager:
                    related_wrapper = manager[related]
                    self.many_to_one[field.name] = related_wrapper
                    related_wrapper.register_related('one_to_many', self)
                continue
            elif isinstance(field, (OneToOneField,)):
                related = field.name
                if related in manager:
                    related_wrapper = manager[related]
                    self.one_to_one[field.name] = related_wrapper
                    related_wrapper.register_related('one_to_one', self)
                continue
            self.fields.append(field.name)

        # find related fields
        for key, field in self.model.__dict__.items():
            if isinstance(field, (ForeignRelatedObjectsDescriptor, )):
                dict_ = self.one_to_many
                remote = 'many_to_one'
            elif isinstance(field, (SingleRelatedObjectDescriptor)):
                if issubclass(field.related.model, self.model.__class__):
                    dict_ = self.children
                    remote = 'parent' 
                else:
                    dict_ = self.one_to_one
                    remote = 'one_to_one'
                related = field.related.model.__name__
            elif isinstance(field, (ReverseSingleRelatedObjectDescriptor)):
                # field points to 1:M or 1:1
                field = field.field
                if isinstance(field, (ForeignKey, )):
                    dict_ = self.many_to_one
                    remote = 'one_to_many'
                else:
                    dict_ = self.one_to_one
                    remote = 'one_to_one'
            else:
                #not a related field
                continue
            
            # register related field, only if it has already been registered.
            related = field.related.model.__name__
            if related in manager:
                related_wrapper = manager[related]
                dict_[related_wrapper.name()] = related_wrapper
                related_wrapper.register_related(remote, self)

    
    def register_related(self, dict_, wrapper):
        """
        register a related object.  used by other wrappers to update the other
        side of a relationship.
        
        @param wrapper
        @param name
        """        
        self.__dict__[dict_][wrapper.name()] = wrapper


class ModelManager(Plugin, PluginManager):
    """
    Manager for tracking enabled models
    """
    depends = TypeManager
    description = 'Manages enabled models'
    objects = (ObjectType(ModelBase, ModelWrapper))
    
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        PluginManager.__init__(self)



def generic_model_list_view(request, model, owner=None):
    # get permissions on this class of object
    profile = request.user.getProfile()
    perms = profile.get_object_permissions(model)
    
    if not perms:
        return render_to_response('no_perms.html')
    
    query = model.objects.all()
    # check for permissions on the model directly.  This supercedes all other
    # permissions. If there are permissions on the model, then no other joins
    # are needed for filtering records
    if not filter(perms, lambda x:len(x[0])==1):
        # no direct perms found. Convert all perms to Q clauses.  These clauses
        # must walk the relations backwards to the owner.
        #
        # TODOs: There may be multiple paths that result in different records
        # 1) need to figure out how to reduce the number of paths if possible
        # 2) need to figure out if multiple paths can conflict
        for perm in perms:
            owner_path = '__'.join(perm)
            Q(**{owner_path:user})

    return render_to_response('model_list_view.html', {'records':query})


class ModelListView(View):
    """
    Generic view generated for a model.  For this view to function the model
    must also be registered.
    """
    handler = generic_model_list_view
    def __init__(self, model):
        self.model = model


class ModelView(View):
    """
    Generic view for displaying instances of a model
    """
    
    def __init__(self, model):
        """
        @param model - ModelWrapper
        """
        self.model = model
    
    def __call__(self, request, id):
        """
        Overridden to process the requests directly rather delegating to another
        function
        """
        user = request.user.getProfile()
        perms = self.model.has_perms(user, id)
        
        if perms & PERM_READ != PERM_READ:
            return render_to_response('no_perms.html')
        
        instance = self.model.get(id=id)
        c = RequestContext(request, processors=[settings_processor])
        return render_to_response('view/generic_model_view.html',
            {'wrapper': self.model, 'instance':instance}, context_instance=c)
