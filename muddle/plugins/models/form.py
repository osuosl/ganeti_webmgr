from django import forms
from django.db.models import fields

from muddle.util import dict_key

FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    fields.DateTimeField: {
        'form_class': forms.SplitDateTimeField,
    },
    fields.DateField:    {'form_class': forms.DateField},
    fields.TimeField:    {'form_class': forms.TimeField},
    fields.TextField:    {'form_class': forms.CharField},
    fields.URLField:     {'form_class': forms.URLField},
    fields.IntegerField: {'form_class': forms.IntegerField},
    fields.CharField:    {'form_class': forms.CharField},
    #models.ImageField:   {'form_class': widgets.AdminFileWidget},
    #models.FileField:    {'form_class': widgets.AdminFileWidget},
}


class CompositeFormBase(forms.Form):
    """
    A form object that contains a single form composited from multiple models.
    This is used as a base for Forms generated from a combination of
    ModelWrapper and User Permissions.
    """    

    def __init__(self, initial=None):
        super(CompositeFormBase, self).__init__(initial)
            
        self.one_to_one_instances = {}
        for k in self.one_to_one.keys():
            self.one_to_one_instances[k] = self.one_to_one[k](initial)
            
        self.one_to_many_instances = {}
        for k in self.one_to_many.keys():
            self.one_to_many_instances[k] = self.one_to_many[k](initial)
            
    def is_valid(self):
        """
        Validate form and all formsets
        """
        if not super(CompositeFormBase, self).is_valid():
            return False
        for k in self.one_to_one_instances.keys():
            if not self.one_to_one_instances[k].is_valid():
                return False
        for form in self.one_to_many_instances:
            if not form.is_valid():
                return False
        return True

    def save(self):
        """
        Save model and all related models
        """
        if not self.is_valid():
            raise Exception(self.errors)
            
        data = self.cleaned_data
        if self.pk in self.data:
            instance = self.model.objects.get(pk=data[self.pk])
        else:
            instance = self.model()
        instance.__dict__.update(self.data)
        instance.save()
        
        for form in self.one_to_one_instances.values():
            form.save(instance)

        for form in self.one_to_many_instances.values():
            form.save(instance)


class Related1To1Base(forms.Form):
    """
    Base class for sub-forms generated for 1:1 relationships
    """
    def save(self, related):
        try:
            instance = self.model.objects.get(**{self.fk:related})
        except self.model.DoesNotExist:
            instance = self.model()
            instance.__setattr__(self.fk, related)
        instance.__dict__.update(self.cleaned_data)
        instance.save()


class ModelEditView(object):
    """
    Class that dynamically creates a form and formsets based on ModelWrapper
    """
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.exclude = []

    def get_form(self, user=None):
        """
        Creates a FormClass from modelwrapper information and user permissions
        """
        # get form from cache if available, else rebuild the form
        attrs = self._get_form()
        
        # filter out permissions that the user doesn't have
        # this is done here so that attrs may be cached
        
        klass = type('DynamicModelClass', (CompositeFormBase,), attrs)
        return klass

    def _get_form(self):
        """
        Internal function that creates the form class.  This is separate from
        get_form() to allow caching.
        
        @returns dictionary of attributes for creating form class
        """
        w = self.wrapper
        exclude = lambda x: x not in self.exclude
        attrs = {
            'pk':w.pk,
            'model':w.model
            }
        
        self.get_fields(attrs, w)

        one_to_one = {}
        for k in filter(exclude, w.one_to_one.keys()):
            inner_attrs = {
                    'label':k,
                    'fk':dict_key(w.one_to_one[k].one_to_one, w),
                    'model':w.one_to_one[k].model
                    }
            self.get_fields(inner_attrs, w.one_to_one[k])
            one_to_one[k] = type('FormClass', (Related1To1Base,), inner_attrs)
        attrs['one_to_one'] = one_to_one

        one_to_many = {}
        for k in w.one_to_many.keys():
            one_to_many[k] = self.get_formset(w.one_to_many[k])
        attrs['one_to_many'] = one_to_many

        return attrs

    def get_fields(self, attrs, wrapper, path=[], recurse=0):
        """
        Gets all fields for the given wrapper
           * adds direct fields
           * recurses into parents adding their fields
           * recurses into children adding their fields
           * adds M:1 (foreign key) relations
        """
        if recurse > -1 and wrapper.parent:
            # we're parsing an object starting with the child.  Get the parent
            # fields too
            for k in wrapper.parent.keys():
                self.get_fields(attrs, wrapper.parent[k], path, recurse=1)
        
        for k in wrapper.fields.keys():
            attrs[k] = self.get_form_field(wrapper.fields[k], path)
        
        for k in wrapper.many_to_one:
            field = wrapper.fk[k]
            attrs[field.attname] = self.get_fk_field(
                                            wrapper.many_to_one[k].model,
                                            k, field, path)

        if recurse < 1 and wrapper.children:
            # we're parsing the an object starting with the parent.  Get the
            # childs fields too.
            for k in wrapper.children.keys():
                self.get_fields(attrs, wrapper.children[k], path, recurse=-1)

    def get_form_field(self, field, path):
        """
        Gets a FormField given the ModelField and options
        """
        options = {}
        options.update(FORMFIELD_FOR_DBFIELD_DEFAULTS[field.__class__])
        #options = {} #TODO lookup options using path
        klass = options['form_class']
        del options['form_class']
        
        return klass(**options)

    def get_fk_field(self, model, label, field, path=None):
        """
        Gets a choice field for a ForeignKey relationship.
        
        @param model - related model
        """
        defaults = {
            'label':label,
            'queryset':model.objects.all(),
            'required':field.null
        }

        #TODO lookup options using path
        options = {}
        defaults.update(options)
        
        klass = forms.ModelChoiceField
        return klass(**defaults)

    def get_formset(self, wrapper, path=None):
        """
        Returns a BaseInlineFormSet class for use in admin add/change views.
        """
        fields = None
        exclude = []
        
        defaults = {
            "form": self.form,
            "formset": self.formset,
            "fk_name": self.fk_name,
            "fields": fields,
            "exclude": (exclude + kwargs.get("exclude", [])) or None,
            "formfield_callback": curry(self.get_form_field, path=path),
            "extra": self.extra,
            "max_num": self.max_num,
        }
        #defaults.update(path)
        return inlineformset_factory(self.parent_model, self.model, **defaults)

    def __call__(self, request, id=None):
        klass = self.get_form(request.user.get_profile())
        if request.POST:
            #process form
            form = klass(request.POST)
            if form.is_valid():
                self.process_form(form)
            
        elif id:
            # fill form values from model instance
            form = klass()
        else:
            # unbound form
            form = klass()