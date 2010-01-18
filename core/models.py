import cPickle

from django.db import models


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
        
        if not isinstance(form_class, (list, tuple)):
            form_class = (form_class,)
        
        config = {}
        for class_ in form_class:
            for name, field in class_.base_fields.items():
                config[name] = field.initial
        self.config = config
    
class PluginManagerSession(models.Model):
    """
    Stores data about a plugin session.  When deployed in a production
    environment behind apache, there will be as many instances of the app as
    there are apache threads.  PluginManagerSessions are used to synchronize
    configuration changes to Plugins.
    """
    last_update = models.DateTimeField()
    

class PluginConfigChange(models.Model):
    """
    Stores data about changes to plugin configuration.  This includes enabling
    or disabling a plugin, or changes to their configuration blob.
    
    instances of this class only persist until all active Sessions have received
    the changes.  New sessions will pull data directly from the database.
    """
    time = models.DateTimeField()
    change = models.CharField(max_length=256)