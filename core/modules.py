




class PluginManager(object):
    """
    Manages the lifecycle of plugins.  Plugins may be registered making the
    manager aware of the plugin.  The plugins may then be enabled or disabled.
    """
    
    def __init__(self, plugins):
        self.plugins = {}
        self.enabled = {}
    
    
    def register_plugin(self, plugin):
        """
        Registers a plugin with this manager.  Plugins are stored by __name__
        so that they may be looked up later.  Registration just makes them
        available to use on this installation, they don't add any functionality
        or check dependencies until they are enabled with enable_plugin()
        
        @param plugin - plugin class to register
        """
        self.plugins[plugin.__name__] = plugin


    def register_plugins(self, plugins):
        """
        Registers a collection of plugins
        """
        for plugin in plugins:
            self.register(plugin)


    def enable_plugin(plugin):
        """
        Enables a plugin allowing it to register its objects and or plugins
        for existing objects.  This also enables all dependencies returned by
        get_depends(plugin).
        
        If the plugin or any depends are 
        
        @param plugin - name of plugin to register
        """
        class_ = self.plugins[plugin]

        # as long as get_depends() returns the list in order from eldest to
        # youngest, we can just iterate the list making sure each one is enabled
        # if they all succeed then the plugin can also be enabled.
        for depend in get_depends(plugin):
            
            if depend.__name__ in self.enabled:
                continue
            
        
        instance = class_()
        
    
    
    def autodiscover(self, root):
        """
        scans directories for plugins.  all plugins are registered with this
        manager.
        """
        self.register_plugins(self.scan_directories())


class Plugin(object):
    """
    A Plugin is something that provides new functionality to PROJECT_NAME.  A
    plugin may register various objects such as Models, Views, and Processes
    or register plugins to existing objects
    
    Dependencies are created by 
    """
    
    depends = None
    
    def __init__(self, manager):
        """
        Creates the plugin.  Does *NOT* initialize the plugin.  This should only
        set configuration.
        """
        pass
    
    def initialize(self):
        pass

    
def get_depends(class_, descendents=set()):
    """
    Gets a list of dependencies for this plugin, including recursive
    dependencies.  Dependencies will be sorted in order in which they need to
    be loaded
    
    @param class_ - class to get depends for
    @param child - child class that is requesting depends for a parent.  Used
    to check for cyclic dependency errors.
    @returns list of dependencies if any, else empty list
    """
    def add(value, set):
        """Helper Function for set-like lists"""
        if value not in set:
            set.append(value)
            
    # initial type checking
    if not class_.depends:
        return []
    elif not isinstance(class_.depends, (tuple, list)):
        class_depends = set((class_.depends,))
    else:
        class_depends = set(class_.depends)
        
    # check for cycles.  As we recurse into dependencies (parents) we build a
    # list of the path we took.  If at any point a parent depends on something
    # already on the list, its a cycle.
    descendents_ = set([class_]).union(descendents)
    if descendents_ and not descendents_.isdisjoint(class_depends):
        raise CyclicDependencyException(class_.__name__)

    # recurse into dependencies of parents (grandparents) checking all of them
    # and adding any that are found.  ancestors are added before descendents
    # to ensure proper loading order
    _depends = []
    for parent in class_depends:
        grandparents = get_depends(parent, descendents_)
        if grandparents:
            for grandparent in grandparents:
                add(grandparent, _depends)
        add(parent, _depends)
        
    return _depends


class CyclicDependencyException(Exception):
    """
    Exception thrown when a cycle is detected within dependencies of a module
    """
    pass


class Example(Plugin):
    def initialize():        
        register(Client, Server)
        register(Client, VirtualMachine)
        register((Server,VirtualMachine), IPAddress)
        