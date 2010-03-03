from django import forms
from django.forms.extras import widgets
from django.db.models import fields
from django.shortcuts import render_to_response
from django.template import RequestContext

from muddle import settings_processor
from muddle.plugins.models.wrapper import ModelWrapper
from muddle.plugins.view import View
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
        
        self.form_instance = self.form(initial)
        self.one_to_one_instances = {}
        for k in self.one_to_one.keys():
            self.one_to_one_instances[k] = self.one_to_one[k](initial)
            
        self.one_to_many_instances = {}
        for k in self.one_to_many.keys():
            self.one_to_many_instances[k] = self.one_to_many[k](initial)
    
    def is_valid(self):
        """
        Validate form and all formsets.  This also sets self.errors to a dict
        of errors from all children
        """
        valid = True
        errors = {'form':None, 'one_to_one':{}, 'one_to_many':{}}
        if not self.form_instance.is_valid():
            valid = False
            errors['form'] = self.form_instance.errors
        for k in self.one_to_one_instances:
            if not self.one_to_one_instances[k].is_valid():
                valid = False
                errors['one_to_one'][k] = self.one_to_one_instances[k].errors
        for k in self.one_to_many_instances:
            if not self.one_to_many_instances[k].is_valid():
                valid = False
                errors['one_to_many'][k] = self.one_to_many_instances[k].errors
        
        # set using dict as form does something wierd to prevent setting it
        self.__dict__['errors'] = None if valid else errors
        return valid

    def save(self):
        """
        Save model and all related models
        """
        if not self.is_valid():
            raise Exception(self.errors)
        
        instance = self.form_instance.save()
        for form in self.one_to_one_instances.values():
            form.save(instance)
        for form in self.one_to_many_instances.values():
            form.save(instance)


class ModelFormBase(forms.Form):
    """
    Base Form class for basic models.  This form is capable of creating and
    updating instances of the associated model.
    """
    def save(self):
        """
        Creates or saves an instance of this forms model using the form data
        """
        data = self.cleaned_data
        if self.pk in self.data:
            instance = self.model.objects.get(pk=data[self.pk])
        else:
            instance = self.model()
        instance.__dict__.update(self.data)
        instance.save()
        return instance


class Related1To1Base(forms.Form):
    """
    Base class for sub-forms generated for 1:1 relationships.  This subclass
    has a single form object and instance.
    """
    def __init__(self, initial=None):
        super(Related1To1Base, self).__init__(initial)
        self.form_instance = self.form(initial)
    
    def is_valid(self):
        _super = super(Related1To1Base, self).is_valid()
        return self.form_instance.is_valid() and _super
    
    def save(self, related):
        """
        Updates an existing object if there is already a related object.  Else
        it creates a new instance. Field prefixes are stripped off the values
        as they are unpacked
        """
        try:
            instance = self.model.objects.get(**{self.fk:related})
        except self.model.DoesNotExist:
            instance = self.model()
            instance.__setattr__(self.fk, related)
        data = self.form_instance.cleaned_data
        i = len(self.prefix_)
        for k in data:
            instance.__setattr__(k[i:], data[k])
        instance.save()


class Related1ToMBase(forms.Form):
    """
    Base class for sub-forms generated for 1:M relationships.  This form can
    have multiple instances of the contained form.
    """
    def __init__(self, initial):
        super(Related1ToMBase, self).__init__(initial)
        count = initial[self.count]
        count = count+self.extra if count+self.extra < self.max_num else self.max_num
        self.instances = [self.get_instance(i, initial) for i in range(count)]
    
    def get_instance(self, index, initial):
        attrs = {}
        for k, v in self.attrs.items():
            attrs['%s_%d' % (k,index)] = v
        return type('Related1ToMSubForm', (forms.Form,), attrs)(initial)


class ParentBase(forms.Form):
    """
    Base class for a form encapsulating a parent class and its descendents. Each
    child class will have a sub-form.  One of the subforms will be selected.
    
    If there are several levels of children (ie. C->B->A) the tree is flattened.
    A grandchild is still a child, even if indirect.
    """
    def __init__(self, initial=None):
        """
        Initializes self, and all children
        """
        super(ParentBase, self).__init__(initial)
        instances = {}
        for k in self.children:
            instances[k] = self.children[k](initial)
        self.instances = instances
    
    def save(self):
        """
        Save the selected child form, else save the parent.  When saving a child
        model parent values are copied into the child.  Django handles saving
        the parent internally
        """
        key = self.data['%s_selected_child' % self.prefix_]
        if key:
            form = self.instances[key]
        else:
            form = self
        
        if form.pk in self.data:
            instance = form.model.objects.get(pk=data[form.pk])
        else:
            instance = form.model()
        
        # add parent data
        data = self.cleaned_data
        i = len(self.prefix_)
        for k in data:
            instance.__setattr__(k[i:], data[k])

        if key:
            data = form.cleaned_data
            i = len(form.prefix_)
            for k in data:
                instance.__setattr__(k[i:], data[k])
        
        instance.save()
        return instance
    
    def is_valid(self):
        """
        validate only the selected child form
        """
        valid = super(ParentBase, self).is_valid()
        errors = {} if valid else {'parent':self.errors}
        key = self.data['%s_selected_child' % self.prefix_]
        if key:
            child = self.instances[key]
            if not child.is_valid():
                valid = False
                self.errors['child'] = child.errors
        return valid


class ModelEditView(View):
    """
    Class that dynamically creates a form and formsets based on ModelWrapper
    """
    def __init__(self, wrapper):
        """
        @param model - Model or ModelWrapper
        """
        self.wrapper = wrapper
        self.exclude = []
        
        if self.wrapper.__class__ == ModelWrapper:
            self.regex = '^%s/(\d+)/Edit$' % self.wrapper.name()
        else:
            self.regex = '^%s/(\d+)/Edit$' % self.wrapper.__name__
    
    def __call__(self, request, id=None):
        #klass = self.get_form(request.user.get_profile())
        klass = self.get_form(None)
        if request.POST:
            #process form
            form = klass(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect()
            
        elif id:
            # fill form values from model instance
            instance = self.wrapper.model.objects.get(pk=id)
            data = {}
            data.update(instance.__dict__)
            for field, fw in self.wrapper.one_to_one.items():
                related = instance.__getattribute__(field)
                if fw.children:
                    for k,v in fw.children.items():
                        try:
                            child = related.__getattribute__(k)
                            for n,cv in child.__dict__.items():
                                data['%s_%s' % (k, n)] = cv
                            data['%s_selected_child' % field] = v.name()
                            break
                        except v.model.DoesNotExist:
                            pass
                else:
                    for k,v in related.__dict__.items():
                        data['%s_%s' % (field, k)] = v
                        
            for field, fw in self.wrapper.one_to_many.items():
                related = instance.__getattribute__(field).all()
                count = 0
                for one_to_many in related:
                    for k,v in one_to_many.__dict__.items():
                        data['%s_%s_%d' % (field, k, count)] = v
                        count += 1
                data['%s_count' % field] = len(related)
                
            form = klass(data)
        else:
            # unbound form
            form = klass()
        
        c = RequestContext(request, processors=[settings_processor])
        return render_to_response('edit/generic_model_edit.html', \
            {'wrapper':self.wrapper, 'form':form}
            , context_instance=c)

    def get_form(self, user=None):
        """
        Creates a FormClass from modelwrapper information and user permissions
        """
        # get form from cache if available, else rebuild the form
        attrs = self._get_form()
        
        # filter out permissions that the user doesn't have
        # this is done here so that attrs may be cached
        
        klass = type('CompositeModelForm', (CompositeFormBase,), attrs)
        return klass

    def _get_form(self):
        """
        Internal function that creates the form class.  This is separate from
        get_form() to allow caching.
        
        @returns dictionary of attributes for creating form class
        """
        w = self.wrapper
        exclude = lambda x: x not in self.exclude
        form = self.form_factory(w)

        one_to_one = {}
        for k in filter(exclude, w.one_to_one.keys()):
            inner_attrs = {
                    'label':k,
                    'fk':dict_key(w.one_to_one[k].one_to_one, w),
                    'prefix_':'%s_' % k,
                    'model':w.one_to_one[k].model,
                    'form':self.form_factory(w.one_to_one[k], k)
                    }
            one_to_one[k] = type('Related1To1Form', (Related1To1Base,), inner_attrs)

        one_to_many = {}
        for k in w.one_to_many.keys():
            one_to_many[k] = self.get_formset(w.one_to_many[k], k)

        return {
            'model':w.model,
            'form':form,
            'one_to_one':one_to_one,
            'one_to_many':one_to_many
            }

    def form_factory(self, wrapper, prefix=''):
        """
        Build a basic Form if possible, else it returns a parent form
        """
        if wrapper.children:
            return self.get_parent_form(wrapper, prefix=prefix)
        return self.get_vanilla_form(wrapper, prefix=prefix)

    def get_vanilla_form(self, wrapper, path=[], prefix=''):
        attrs = {'model':wrapper.model, 'pk':wrapper.pk}
        return type( 'ModelForm', (ModelFormBase,), \
            self.get_fields(wrapper, attrs, path, prefix=prefix))

    def get_parent_form(self, wrapper, path=[], prefix=''):
        """
        Build a form for a model that has child classes
        """
        children = {}
        recurse = {}
        for k in wrapper.children.keys():
            child = wrapper.children[k]
            self.get_child_form(wrapper, k, child, children, recurse)
        attrs = {
            'children':children,
            'recurse':recurse,
            'prefix_':prefix,
            'pk':wrapper.pk,
            'model':wrapper.model,
            '%s_selected_child' % prefix:forms.CharField(max_length=64, required=False, widget=forms.HiddenInput(attrs={'class':'selecter'}))
            }
        self.get_fields(wrapper, attrs, path, prefix=prefix)
        return type('ParentModelForm', (ParentBase,), attrs)

    def get_child_form(self, root, prefix, wrapper, children, recurse, path=[]):
        attrs = {'model':wrapper.model, 'pk':wrapper.pk, 'prefix_':'%s_'%prefix}
        children[wrapper.name()] = type( 'ModelForm', (ModelFormBase,), \
            self.get_fields(wrapper, attrs, path, False, prefix))
        
        for parent in wrapper.parent.values():
            if parent != root and issubclass(parent.model, (root.model,)):
                recurse[wrapper.name()] = parent.name()
        
        for k in wrapper.children.keys():
            child = wrapper.children[k]
            self.get_child_form(root, k, child, children, recurse)

    def get_fields(self, wrapper, attrs=None, path=[], parent=True, prefix=''):
        """
        Gets all fields for the given wrapper
           * adds direct fields
           * recurses into parents adding their fields
           * adds M:1 (foreign key) relations
        """
        attrs = {} if attrs == None else attrs
        prefix = '%s_' % prefix if prefix and prefix[-1]!='_' else prefix
        
        if parent and wrapper.parent:
            # we're parsing an object starting with the child.  Get the parent
            # fields too
            for k in wrapper.parent.keys():
                self.get_fields(wrapper.parent[k], attrs, path, prefix=prefix)
         
        for k in wrapper.fields.keys():
            attrs['%s%s' % (prefix, k)] = self.get_form_field(wrapper.fields[k], path, label=k)
        
        for k in wrapper.many_to_one:
            field = wrapper.fk[k]
            attrs['%s%s' % (prefix, field.attname)] = self.get_fk_field(
                                            wrapper.many_to_one[k].model,
                                            k, field, path)
        return attrs

    def get_form_field(self, field, path, **kwargs):
        """
        Gets a FormField given the ModelField and options
        """
        options = {}
        options.update(FORMFIELD_FOR_DBFIELD_DEFAULTS[field.__class__])
        options.update(kwargs)
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

    def get_formset(self, wrapper, prefix, path=None):
        """
        Returns a Related1ToMBase class for use displaying 1:M forms
        """
        fields = None
        exclude = []
        
        attrs = {
            #"fk_name": self.fk_name,
            "count":'%s_count' % prefix,
            "extra": 1,
            "max_num": 10,
            "attrs":self.get_fields(wrapper, prefix=prefix)
        }
        
        return type('Related1ToMForm', (Related1ToMBase,), attrs)
    
    def name(self):
        if self.wrapper.__class__ == ModelWrapper:
            return 'EditView:%s' % self.wrapper.name()
        return 'EditView:%s' % self.wrapper.__name__
    
    def _register(self, manager):
        if self.wrapper.__class__ != ModelWrapper:
            self.wrapper = manager.manager['ModelManager'][self.wrapper.__name__]
