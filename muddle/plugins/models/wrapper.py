from django.db.models.base import ModelBase
from django.db.models.fields import AutoField
from django.db.models.fields.related import *

from muddle.plugins.registerable import *


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
        self.fields = {}
        self.one_to_many = {}
        self.many_to_one = {}
        self.one_to_one = {}
        self.children = {}
        self.parent = {}
        self.pk = None
        self.fk = {}

    def _deregister(self, manager):
        """
        Remove relations from all related objects
        @param manager - manager this plugin is registered to
        """
        for wrapper in self.one_to_one.values():
            wrapper.deregister_related('one_to_one', self)
        for wrapper in self.one_to_many.values():
            wrapper.deregister_related('many_to_one', self)
            wrapper.deregister_related('one_to_many', self)
        for wrapper in self.many_to_one.values():
            wrapper.deregister_related('one_to_many', self)
        for wrapper in self.children.values():
            wrapper.deregister_related('parent', self)
        for wrapper in self.parent.values():
            wrapper.deregister_related('children', self)

    def deregister_related(self, dict_, wrapper):
        """
        deregister a related object.  used by other wrappers to update the other
        side of a relationship.
        @param dict_ - dictionary to add the wrapper to
        @param wrapper - wrapper to be removed 
        """
        dict_ = self.__dict__[dict_]
        for key, value in dict_.items():
            if value == wrapper:
                del dict_[key]
                break
    
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
        perms = owner.get_permissions(self.name()).items()
        possible = mask if mask else wrapper.permissions
        # iterate while there are keys !possessed and permissions left to check
        while possible & possess != possible and perms:
            path, perm = perms.pop()
            if possess ^ perm:
                # permission in perm that is not already possessed, check it
                if path == None:
                    # perm directly on model, nothing to check
                    possess = possess | perm
                    continue
                elif path[-1] == '1':
                    # path originates with an owner
                    clause = {str('%s__in' % '__'.join(path[:-1])):(owner,)}
                else:
                    # path originates with a model, not an owner
                    clause = {str('%s__isnull' % '__'.join(path)):False}
                if self.model.objects.filter(id=id).filter(**clause).count():
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
                self.pk = field
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
            self.fields[field.name] = field
        
        # find related fields
        for key, field in self.model.__dict__.items():
            if isinstance(field, (ForeignRelatedObjectsDescriptor,)):
                dict_ = self.one_to_many
                remote = ('many_to_one', field.related.field.name, self)
                related = field.related.model.__name__
            elif isinstance(field, (SingleRelatedObjectDescriptor,)):
                if issubclass(field.related.model, (self.model,)):
                    dict_ = self.children
                    remote = ('parent', field.related.field.name, self)
                else:
                    dict_ = self.one_to_one
                    remote = ('one_to_one', field.related.field.name, self)
                related = field.related.model.__name__
            elif isinstance(field, (ManyRelatedObjectsDescriptor,)):
                dict_ = self.one_to_many
                remote = ('one_to_many', field.related.field.name, self)
                related = field.related.model.__name__
            elif isinstance(field, (ReverseSingleRelatedObjectDescriptor,
                                    ReverseManyRelatedObjectsDescriptor)):
                # field points to 1:M or 1:1
                related = field.field.rel.to.__name__
                if isinstance(field.field, (OneToOneField, )):
                    to = field.field.rel.to
                    if issubclass(self.model, (to,)):
                        dict_ = self.parent
                        remote=('children',field.field.related_query_name(),self)
                    else:
                        dict_ = self.one_to_one
                        remote =('one_to_one',field.field.related_query_name(),self)
                elif isinstance(field.field, (ForeignKey)):
                    dict_ = self.many_to_one
                    self.fk[key] = field.field
                    remote = ('one_to_many', field.field.related_query_name(), self)
                elif isinstance(field.field, (ManyToManyField,)):
                    dict_ = self.one_to_many
                    remote = ('one_to_many', field.field.related_query_name(), self)
            else:
                #not a related field
                continue
                
            # register related field, only if it has already been registered.
            if related in manager:
                related_wrapper = manager[related]
                dict_[key] = related_wrapper
                related_wrapper.register_related(*remote)

    def register_related(self, dict_, key, wrapper):
        """
        register a related object.  used by other wrappers to update the other
        side of a relationship.
        @param dict_ - dictionary to add the wrapper to
        @param key - field name on this model
        @param wrapper - wrapper that is being added
        """        
        self.__dict__[dict_][key] = wrapper

    def __str__(self):
        return '<ModelWrapper @ %s : %s>' % (hex(id(self)), self.name())

