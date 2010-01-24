class Registerable(object):
    """
    Base class for objects that can be registered with
    """
    target = None
    _target = None

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


class View(Registerable):
    """
    Base class for building user interface
    """
    pass