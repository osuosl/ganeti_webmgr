PERMS_ALL   = 0b1111
PERMS_NONE  = 0b0000
PERM_READ   = 0b0001
PERM_WRITE  = 0b0010
PERM_CREATE = 0b0100
PERM_DELETE = 0b1000

class Registerable(object):
    """
    Base class for objects that can be registered with
    """
    target = None
    _target = None
    permissions = PERMS_NONE

    def __init__(self, target=None):
        """
        @param manager - Manager that this object will be registered with.  May
        be a period delimitted string, or iterable of strings corresponding to
        plugin (class) names.
        """
        self.target = target

    def _deregister(self, manager):
        """
        deregisters this Registerable.  This is called by the manager when it
        is deregistering a plugin.  This should not be called directly.  It is
        intended to be used by the plugin to remove references to other objects
        that might be registered with the manager.
        """
        pass

    @classmethod
    def name(class_):
        return class_.__name__

    def _register(self, manager):
        """
        initializes this Registerable.  This is called by the manager when it
        is deregistering a plugin.  This should not be called directly.  It is
        intended to be used by the plugin to obtain references to other objects
        that might be registered with the manager.
        """
        pass

    def __setattr__(self, key, value):
        if key == 'target':
            if isinstance(value, (list,tuple)):
                self._target = value    
            elif isinstance(value, (str,)):
                self._target = value.split('.')    
        super(Registerable, self).__setattr__(key, value)
        
    def has_perms(self, user, mask=None, possess=PERMS_NONE, **kwargs):
        """
        Checks to see if a user has the permissions mask requested.  Checks
        both users and groups
        
        @param user - users to check perms for
        @param id - id of instance to check
        @param mask - permissions mask to check for.  If None search for all
                    perms
        @param possess - permissions already possessed by the owner.
        
        @returns - Logical AND of request mask, and actual mask.  If None it
        will return a mask containing all permissions
        """
        mask = mask if mask else self.permissions
        perms = self._has_perms(user, id, mask, possess, **kwargs)
        if not (perms & mask == mask):
            groups = iter(user.groups)
            try:
                while not (perms & mask == mask): 
                    perms = self._has_perms(groups.next())
            except StopIteration:
                pass
        return perms
        
    def _has_perms(self, permissable, mask=PERMS_NONE, possess=PERMS_NONE):
        """
        Authorize a permissable (usually a user or group) to use this object.
        
        Objects all have a path that identifies their usage.  By default this is
        the path from the rootmanager (implicit) to the
        
        This may be overridden such as is done with models to verify ownership,
        and generic views which delegate to their underlying model.
        """
        
        # TODO: implement this.  there is no ownership so only permissions on
        # this object need to be checked.  The path still matters in case of
        # conflicting object names.  a hash should be used instead to identify
        # the object internally without following a path.
        return PERMS_ALL
    
    
    