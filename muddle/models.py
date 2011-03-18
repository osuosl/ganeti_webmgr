import cPickle
from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


# Models for testing
if settings.DEBUG or True:
    class TestModel(models.Model):
        value = models.IntegerField(null=True)
        value2 = models.IntegerField(null=True)
    class TestModelChild(models.Model):
        value = models.IntegerField(null=True)
        value2 = models.IntegerField(null=True)
        parent = models.ForeignKey(TestModel, null=True)
    class TestModelChildChild(models.Model):
        value = models.IntegerField(null=True)
        value2 = models.IntegerField(null=True)
        parent = models.ForeignKey(TestModelChild, null=True)


class PluginConfig(models.Model):
    """
    Stores the configuration for a plugin.  When plugins are registered they
    create an instance of this class to persist configuration.  This includes
    data tracked for every Plugin, as well as a blob of data specific to the
    individual plugin
    """
    name = models.CharField(max_length=128, unique=True)
    enabled = models.BooleanField(default=False)
    _config = models.TextField(max_length=1024, default='N.', null=True)

    def __init__(self, *args, **kwargs):
        """
        Overridden to unpickle configuration dictionary.  After initialization
        the pickled data is discarded as it is not used anymore.
        """
        super(PluginConfig, self).__init__(*args, **kwargs)
        self.config = cPickle.loads(self._config.__str__())
        self._config = None
    
    def save(self):
        """
        Overridden to pickle configuration dictionary and store in internal
        dictionary.  After saving _config is cleared as calling this function
        again will repeat the pickling.
        """
        self._config = cPickle.dumps(self.config)
        super(PluginConfig, self).save()
        self._config = None
    
    def set_defaults(self, form_class):
        """
        function for setting default values based on the default values within
        a form class
        
        @param form_class - a Form, or list/tuple of Form classes
        """
        if not form_class:
            self.config = None
            return
        
        if not isinstance(form_class, (list, tuple)):
            form_class = (form_class,)
        
        config = {}
        for class_ in form_class:
            for name, field in class_.base_fields.items():
                config[name] = field.initial
        self.config = config


class AppSettingsCategory(models.Model):
    """
    model for storing settings for an app.  This class
    """
    name = models.CharField(max_length=256)


class AppSettingsValue(models.Model):
    """
    An individual app setting value.
    """
    category = models.ForeignKey(AppSettingsCategory, related_name='values')
    key = models.CharField(max_length=64)
    serialized_data = models.CharField(max_length=512)

    @property
    def data(self):
        if self._data:
            self._data = cPickle.loads(self.serialized_data)
        return self._data

    @data.setter
    def data(self, value):
        # clear serialized data, don't know if we'll need to save it
        self.serialized_data = None
        self._data = value
    
    def save(self, *args, **kwargs):
        if self.serialized_data is None:
            self.serialized_data = cPickle.dumps(self._data)
        super(AppSettingsValue, self).save(*args, **kwargs)