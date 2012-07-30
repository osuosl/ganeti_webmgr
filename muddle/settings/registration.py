import cPickle
from django.conf import settings
from muddle.core.apps.plugins import load_app_plugin
from muddle.core.forms.aggregate import AggregateForm
from muddle.settings.models import AppSettingsValue

__all__ = ['initialize', 'register', 'AppSettings']

DEFAULT_CATEGORY = getattr(settings, 'DEFAULT_CATEGORY', 'general')

SETTINGS = {}
"""
stores form classes that define settings in each category.  A settings category
may be a single form or a dictionary of forms, with the keys indicating
sub-categories.  If there is only one sub-category it will be rendered as if
there were no sub-categories
"""

def initialize():
    """
    Initialize the app settings module
    """
    load_app_plugin('muddle.settings')


def register(category, form, subcategory=DEFAULT_CATEGORY):
    """
    Register a form as part of a category and subcategory for settings.

    If there are multiple forms for a given subcategory then they will be
    merged using an AggregateForm.

    If there is only a single subcategory it will be rendered as if there is
    only a single category, but accesses with its explicit location

    @param category: name of category to register form under
    @param form: form class being registered
    @param subcategory: name of subcategory to register form under
    """
    if category not in SETTINGS:
        subcategories = {subcategory:form}
        SETTINGS[category] = subcategories
    else:
        category = SETTINGS[category]
        if subcategory not in category:
            category[subcategory] = form
        else:
            forms = category[subcategory]
            if issubclass(forms, (AggregateForm, )):
                # is already an aggregate form.  aggregate the form into this
                # a new aggregate form
                forms = forms.form_classes
            else:
                forms = [forms]
            forms.append(form)
            category[subcategory] = AggregateForm.aggregate(forms)


class AppSettingsLoader(object):
    """
    class that encompasses settings.
    """

    def __init__(self):
        self._categories = {}

    def __getattribute__(self, key):
        """
        overloaded to allow dynamic checking of properties
        """
        try:
            return super(AppSettingsLoader, self).__getattribute__(key)
        except AttributeError:
            if key in SETTINGS:
                category = Category(key)
                self._categories[key] = category
                return category


class Category(object):
    """
    class that encompasses settings.
    """

    def __init__(self, name):
        self.name = name
        self._category_names = SETTINGS[name]

    def __getattribute__(self, key):
        """
        overloaded to allow dynamic checking of properties
        """
        if key != '_category_names' and key in self._category_names:
            return Subcategory(self, key)
        
        return super(Category, self).__getattribute__(key)


class Subcategory(object):
    """
    class that encompasses settings.
    """
    _data = False
    _fields = None

    def __init__(self, parent, name):
        self._data = None
        self._name = name
        self._full_name = '.'.join([parent.name, name])
        self._fields = parent._category_names[name].base_fields.keys()
        self._load_data()

    def __setattr__(self, key, value):
        if self._data and key in self._fields:
            AppSettingsValue.objects \
                    .filter(category__name=self._full_name, key=key) \
                    .update(serialized_data=cPickle.dumps(value))

        return super(Subcategory, self).__setattr__(key, value)

    def _load_data(self):
        """
        Loads all values for this subcategory.
        """
        values = AppSettingsValue.objects \
                    .filter(category__name=self._full_name) \
                    .values('key', 'serialized_data')
        for value in values:
            setattr(self, value['key'], cPickle.loads(str(value['serialized_data'])))
        self._data = True


AppSettings = AppSettingsLoader()
"""
A global instance of AppSettingsLoader that can be imported where needed
"""