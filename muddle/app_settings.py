from django.conf import settings
from muddle.apps.plugins import load_app_plugin

from muddle.forms.aggregate import AggregateForm


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
    load_app_plugin('muddled_settings')


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
    
    def __init__(self, category, has_data=True):
        self.category = category
        self.has_data = has_data
        self._categories = {}
        self._data = {}
    
    def __getattribute__(self, key):
        """
        overloaded to allow dynamic checking of properties
        """
        if key in self._categories:
            return self._categories[key]

        elif key in SETTINGS:
            loader = AppSettingsLoader(key)
            self._categories[key] = loader

        elif self.has_data:
            # XXX checking properties should be last otherwise data will always
            # be queried on traversal
            if key in self._data:
                return self.data[key]
            else:
                pass

        return super(AppSettings, self).__getattribute__(key)

    def load_data(self, keys):
        """
        utility method for loading multiple data values at once.  This allows
        a single query to be used for loading all of the data
        """
        pass



AppSettings = AppSettingsLoader('')
"""
A global instance of AppSettingsLoader that can be imported where needed
"""