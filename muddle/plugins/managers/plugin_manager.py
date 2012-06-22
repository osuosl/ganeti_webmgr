from muddle.plugins.plugin import Plugin

class PluginManager(object):
    """
    Manages the lifecycle of plugins.  Plugins may be registered making the
    manager aware of the plugin.  The plugins may then be enabled or disabled.
    """
    def __init__(self):
        self.plugins = {}
        self.enabled = self.plugins

    def __contains__(self, key):
        return key in self.enabled

    def deregister(self, plugin):
        """
        deregisters a plugin
        
        @param plugin - name of plugin or plugin itself
        """
        key = plugin if type(plugin) == str else plugin.name()
        print '[Info] Deregistering: ', key
        plugin = self.plugins[key]
        del self.plugins[key]
        plugin._deregister(self)

    def __getitem__(self, key):
        """
        returns an enabled item or this manager if None
        
        @param key - None, a class name, or an iterable of class names
        """
        if key == None:
            return self
        if isinstance(key, (list, tuple)):
            obj = key
            for i in key:
                obj = obj[i]
            return obj
        return self.enabled[key]

    def __len__(self):
        return len(self.enabled)

    def register(self, plugin):
        """
        Registers a plugin with this manager.  Plugins are stored by name
        so that they may be looked up later.
        
        This base is dumb, reserving the following for smarter subclasses:
          * all registered plugins are also enabled.  self.enabled is a
            reference to self.plugins.
          * this class performs no dependency checking.
        
        It will however call plugin.register() to allow it to configure itself
        if needed.  Some plugins, such as Classes, may do nothing when this
        method is called.
        
        @param plugin - plugin object to register
        """
        print '[Info] Registering: ', plugin.name()
        self.plugins[plugin.name()] = plugin
        plugin._register(self)

    def registers(self, plugins):
        """
        Registers a collection of plugins
        @param plugins - iterable of plugins
        """
        for plugin in plugins:
            self.register(plugin)


class PlugableManager(Plugin, PluginManager):
    """
    Manager that is also a plugin
    """
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        PluginManager.__init__(self)
