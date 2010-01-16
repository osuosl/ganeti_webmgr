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
    config = models.TextField(max_length=1024, null=True)
    
    
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