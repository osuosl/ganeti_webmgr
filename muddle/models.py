import cPickle
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

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


class Permissable(models.Model):
    """
    Any object that may be granted permissions.  Base class meant to be extended
    """
    name = models.CharField(max_length=128)
    _permissions = None
    
    def get_permissions(self, target=None):
        """
        returns cached list of compiled permissions
        """
        if not self._permissions:
            self._permissions = self.load_permissions()
        if target:
            try:
                return self._permissions[target]
            except KeyError:
                return {}
        return self._permissions

    def load_permissions(self):
        """
        Permissions are granted to a user directly, and through groups and
        permission groups.  This function aggregates them into a single list
        
        Permissions granted directly are culmulative with permissions granted
        via a PermissionsGroup
        
        Permissions are stored for fast lookup in a dictionary with stucture:
            {TARGET:{PATH:LEVEL}}
        """        
        perms = {}
        for group in self.permission_groups.all():
            group_perms = group.get_permissions()
            for key in group_perms:
                # only update list if key is not in list or is greater
                # perms than what is already in the list
                if key in perms:
                    for path in group_perms[key]:
                        perms[key][path] = perms[key][path] | \
                                                    group_perms[key][path]
                else:
                    perms[key] = group_perms[key]
            
        for perm in self.permissions.all().values_list('path','mask'):
            target, path = Permission.path_list(perm[0])
            if target in perms:
                if path in perms[target]:
                    perms[target][path] = perm[1] | perms[target][path]
                else:
                    perms[target][path] = perm[1] 
            else:
                perms[target] = {path:perm[1]}
        return perms

    def __str__(self):
        return 'Permissable: %s' % self.name

class UserProfile(Permissable):
    """
    Permissions associated directly to a user.  This class does not provide
    authentication, it is intended to be used as the profile object assocated
    with a User in the django authentication system.  This allows us to use
    the other functions of the authentication system, and registration module
    with this custom permissions system.
    """
    user = models.ForeignKey(User, null=True, unique=True)
    admin = models.BooleanField(default=False)

    def __str__(self):
        return 'User: %s' % self.user.name


def create_user_profile(**kwargs):
    """
    Signal handler that creates a UserProfile object when a User account is
    created
    """
    if kwargs['created']:
        profile = UserProfile(user=kwargs['instance'])
        profile.save()
post_save.connect(create_user_profile, sender=User)


class Group(Permissable):
    """
    A group of users.  This may be a client, project or however you decide to
    group your users.  Groups are allowed to create their own subgroups.
    subgroups do not inherit permissions of the parent.
    """
    parent = models.ForeignKey('self', null=True, related_name='groups')
    members = models.ManyToManyField(UserProfile, related_name='groups')

    def __str__(self):
        return 'Group: %s' % self.name

class Permission(models.Model):
    """
    An individual permission.  Permissions grant access to any registered
    object.  Permissions may grant access to an entire collection of objects
    (list of model instances) or to object owned by a group or user.
    
    path - a machine interpretable path from the object the permission grant
    access on to a group or user that owns an object.  If a path contains only
    the target object, then no ownership is required.
    
    level - permission level.  higher level grants more permissions
    granted_to - Permissable object the permission was granted to
    """    
    path = models.CharField(max_length=256)
    mask = models.IntegerField(default=0)       
    granted_to = models.ForeignKey(Permissable, related_name='permissions')

    def __str__(self):
        return 'Permission(%s, %s)' % (self.path, self.mask)
    
    def __setattr__(self, key, value):
        if key == 'path':
            self._path = Permission.path_list(value) if value else None
            self.__dict__['path'] = value
        else:
            super(Permission, self).__setattr__(key, value)
    
    @staticmethod 
    def path_list(path):
        """
        Converts a path to a list of objects
        """
        l = path.split('.')
        if len(l) == 1:
            return path, None
        return l[0], tuple(l[1:])
        
        
class PermissionGroup(Permissable):
    """
    A group of permissions.  Used for creating classes of permissions so that
    they may be granted/remove easier.
    """
    users = models.ManyToManyField(Permissable, related_name='permission_groups')