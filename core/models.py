import cPickle

from datetime import datetime, timedelta

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
            return
        
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
    
    
class SQLLock(models.Model):
    """
    This class stores its lock information in a persistent place that all the
    threads can access.  It allows synchronations across processes.
    
    These locks include an ownership timer in which only one process can acquire
    the lock.  While the lock is owned, no other thread can acquire the lock.
    This is used for locking sections of the interface while a user is editing
    it.
    
    This is a non-blocking lock.  acquire() returns True of False to indicate
    lock ownership
    """
    name = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now=True)
    release_time = models.DateTimeField(null=True)
    acquired = False

    def acquire(self, name, timeout=1000):
        """
        Acquire lock.  
        
        @param timeout [None] - lock times out after this amount of time in
                            milliseconds.  After which
        @param returns True if lock acquired, false otherwise
        """
        self.name = name
        
        # if this instance has timed out, delete it
        if self.id and self.release_time and self.release_time < datetime.now():
            print 'RELEASING!'
            self.release()
        
        # put this instance in contention for the lock if it does not already
        # have an id.
        if timeout:
            self.release_time = datetime.now() + timedelta(0, 0, 0, timeout)
        self.save()
        
        # find the owner, determined by the order in which contenders were
        # created
        contenders = SQLLock.objects.filter(name=self.name).order_by('id')
        owner = contenders[0]
        for owner in contenders:
            if owner.release_time and self.created > owner.release_time:
                # old owner has timed out
                print 'DELETING OLD OWNER'
                owner.delete()
            else:
                break
        self.acquired = owner.id == self.id
        return self.acquired
    
    def release(self):
        self.delete()
        self.id = None
        self.created = None
        self.release_time = None
        self.acquired = False
    