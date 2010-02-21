from django import forms
from django.db.models import fields

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

    def __init__(self, *args, **kwargs):
        pass

    def is_valid(self):
        """
        Validate form and all formsets
        """
        if not super(CompositeFormBase, self).is_valid():
            return False
        for form in self.one_to_one_instances:
            if not form.is_valid():
                return False
        for form in self.one_to_many_instances:
            if not form.is_valid():
                return False
        return True

    def save(self):
        """
        Save model and all related models
        """
        pass


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
        attrs = self._get_form()
        
        #for k in filter(exclude, w.one_to_many.keys()):
        #    self.render_list(formsets, w.one_to_many[k])
        
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
        formsets = []
        attrs = {'formsets':formsets}
        
        self.get_fields(attrs, w)

        one_to_one = {}
        for k in filter(exclude, w.one_to_one.keys()):
            inner_attrs = {'label':k}
            self.get_fields(inner_attrs, w.one_to_one[k])
            one_to_one[k] = type('FormClass', (forms.Form,), inner_attrs)
        attrs['one_to_one'] = one_to_one

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
            attrs[k] = self.get_form_field(k, path)
        
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

    def get_formset(self, request, obj=None, **kwargs):
        """
        Returns a BaseInlineFormSet class for use in admin add/change views.
        
        Copied from django.contrib.admin
        """
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        # if exclude is an empty list we use None, since that's the actual
        # default
        defaults = {
            "form": self.form,
            "formset": self.formset,
            "fk_name": self.fk_name,
            "fields": fields,
            "exclude": (exclude + kwargs.get("exclude", [])) or None,
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
            "extra": self.extra,
            "max_num": self.max_num,
        }
        defaults.update(kwargs)
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