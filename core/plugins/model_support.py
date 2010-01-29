from django.db.models.base import ModelBase
from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, \
                                            SingleRelatedObjectDescriptor

from core.plugins.managers.type_manager import ObjectType, TypeManager
from core.plugins.plugin import Plugin
from core.plugins.plugin_manager import PluginManager
from core.plugins.registerable import Registerable
from core.plugins.view import View


class ModelWrapper(Registerable):
    """
    Wrapper around a django model that stores information used to display it.
    Much of this information is already stored internally to the the model. This
    class provides more convenient and stable api to access it.  This shields
    users of this framework from changes within the django internals.
    """
    target = 'ModelManager'
    _target = ('ModelManager')
    
    def __init__(self, class_):
        """
        @param class_ - model class this is wrapping.
        @param manager - Root manager enabling this wrapper.
        """
        self.model = class_
        self.fields = []
        self.one_to_many = {}
        self.one_to_one = {}
        self.children = {}

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
        del dict_[name]

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
            self.fields.append(field.name)

        # find related fields
        for key, field in self.model.__dict__.items():
            if isinstance(field, (ForeignRelatedObjectsDescriptor, )):
                key_ = self.one_to_many
            elif isinstance(field, (SingleRelatedObjectDescriptor,)):
                if issubclass(field.related.model, self.model.__class__):
                    self._children.append(field.related.model.__name__)
                list_ = self.one_to_one
            else:
                #not a related field
                continue
            # register related field, only if it has already been registered.
            related = field.related.model.__name__
            if False and related in manager.model_manager:
                related_wrapper = manager[related]
                list_[key] = related_wrapper
                related_wrapper.register_related(self)

    def register_related(self, wrapper, name):
        """
        register a related object.  used by other wrappers to update the other
        side of a relationship.
        
        @param wrapper
        @param name
        """
        dict_[name] = wrapper


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




#path client.device.rack

#path ([rack],READ) = no filter

PERM_READ = 1
PERM_WRITE = 2


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


def generic_model_view(request, wrapper, id):
    """
    Handler for displaying an instance of a model
    @param request - HttpRequest object
    @param wrapper - wrapped model to display
    @param id - id of instance to display
    """
    model = wrapper.model
    profile = request.user.getProfile()
    checked_paths = {}
    rw_perm = 0
    
    # rw_perm is the level associated on the model itself.  Only the highest
    # perm needs to be found so it should be checked from highest to lowest
    # 
    # checked paths should also be cached so that queries do not need
    # to be repeated later for other permissions.
    perms = profile.get_object_permissions(model).items()
    if perms:
        object_perms = filter(perms, lambda x: not x[1])
        if object_perms:
            rw_perm = object_perms[1]
        else:
            perms.sort(lambda x,y: x-y)
            for perm in filter(perms, lambda x: x[1]):
                model.objects.filter(**{'__'.join(perm[0]):user}).get(id=id)
            
    # check group perms for higher rw_perm if not already at max
    if rw_perm < 3:
        groups = list(user.groups.objects.all())
        while rw_perm < 3 and groups:
            group = groups.pop()
            perms = group.get_object_permissions(model).items()
            object_perms = filter(perms, lambda x: not x[1])
            if object_perms and rw_perm < object_perms[1]:
                rw_perm = object_perms[1] 
            else:
                perms.sort(lambda x,y: x-y)
                for perm in filter(perms, lambda x: x[1]):
                    model.objects.filter(**{'__'.join(perm[0]):user}).get(id=id)
                    
                    
    # we need to identify what permissions the user has on this object.
    # they can have as many permissions as there are processes defined on the
    # object.  Once permission has been found from any path it is no longer
    # checked.  
    #
    possible_perms = model.processes.keys()
    for possible in possible_perms:
        pass
    
    
    #instance = Device.objects.all()[0]
    
    #wrapper = DjangoModelWrapper(Device)
    c = RequestContext(request, processors=[settings_processor])
    return render_to_response('view/generic_model_view.html',
            {'wrapper': wrapper, 'instance':instance}, context_instance=c)


def check_binary_perms_test(owner, model, possess=0):
    """
    This is a test implementation assuming all perms are encoded in a single
    binary string.  This might not be the case.
    
    Perform a search for permissions.  An owner may have permissions from 
    
    Permissions are stored as a set of binary
    values with each bit representing a permission.  This function performs
    binary operations to compare the set of possible permissions and granted
    permissions for an object.
    
    @param owner - 
    @param model - model to get permissions on
    @param possess - permissions already possessed by the owner
    """
    perms = owner.get_object_permissions(model).items()
    keys = perms.keys()
    possible = wrapper.permissions
    # iterate while there are keys not possessed and permissions left to check
    while not possible & possess and perms:
        path, perm = perms.pop()
        if not possess ^ perm:
            # permission in perm that is not in possess, check it
            try:
                if perm[-1] in ('User','Group'):
                    clause = {'__'.join(perm[0]):None}
                elif len(perm) == 1:
                    possess = possess | perm
                    continue
                else:
                    clause = {'%s__in' % '__'.join(perm[0]):owner}
                model.objects.filter(**clause).get(id=id)
                possess = possess | perm
            except model.DoesNotExist:
                # query didn't return a record
                pass


class ModelView(View):
    """
    Generic view generated for a model.  For this view to function the model
    must also be registered.
    """
    
    handler = generic_model_view
    
    def __init__(self, model):
        self.model = model