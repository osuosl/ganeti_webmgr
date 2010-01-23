from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, \
                                            SingleRelatedObjectDescriptor


class DjangoModelWrapper(object):
    """
    Wrapper around a django model that stores information used to display it.
    Much of this information is already stored internally to the the model. This
    class provides more convenient and stable api to access it.  This shields
    users of this framework from changes within the django internals.
    """
    def __init__(self, class_, manager):
        """
        @param class_ - model class this is wrapping.
        @param manager - Root manager enabling this wrapper.
        """
        self.model = class_
        self.name = class_.__name__
        self.fields = []
        self.one_to_many = {}
        self.one_to_one = {}
        self.children = {}
        self.build_composite_model()
        print self.name

    def build_composite_model(self):
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
                related_wrapper = manager['ModelManager'][related]
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
 
    def deregister_related(self, name):
        """
        deregister a related object.  used by other wrappers to update this
        side of the relationship when they are disabled
        """
        del dict_[name]


class View(object):
    """
    Base class for building user interface
    """
    pass


class DjangoModelView(View):
    pass