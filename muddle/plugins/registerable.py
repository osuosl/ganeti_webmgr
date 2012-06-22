


# define permission masks.  use 2.5 syntax for backwards compatibility
PERM_ALL    = int('1111',2)
PERM_NONE   = int('0000',2)
PERM_READ   = int('0001',2)
PERM_WRITE  = int('0010',2)
PERM_CREATE = int('0100',2)
PERM_DELETE = int('1000',2)

class Registerable(object):
    """
    Base class for objects that can be registered with
    """
    target = None
    _target = None
    permissions = PERM_NONE

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
        
    def has_perms(self, user, mask=None, possess=PERM_NONE, *args, **kwargs):
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
        possess = possess if possess else PERM_NONE
        perms = self._has_perms(user, mask, possess, *args, **kwargs)
        if perms & mask != mask:
            groups = iter(user.groups.all())
            try:
                while perms & mask != mask:
                    perms = self._has_perms(groups.next(), mask, perms, *args, \
                                            **kwargs)
            except StopIteration:
                pass
        return perms
        
    def _has_perms(self, permissable, mask=PERM_NONE, possess=PERM_NONE):
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
        return PERM_ALL
    
    
    