from datetime import datetime, timedelta
from threading import RLock
from multiprocessing.managers import SyncManager

import settings

from core.models import PluginConfig
from core.plugins import CyclicDependencyException, UnknownPluginException
from core.plugins.plugin import Plugin
from core.plugins.registerable import Registerable

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

    def deregister(self, key):
        """
        deregisters a plugin
        """
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

    def registers(self, classes):
        """
        Registers a collection of plugins
        @param plugins - iterable of plugins
        """
        for plugin in plugins:
            self.register(plugin)

    
class RootPluginManager(PluginManager):
    """
    Specialized plugin manager that handles configuration and enabling/disabling
    of all plugins, whether they be registered directly with this plugin or
    are a sub-plugin.
    """
    config = None
    def __init__(self, multi_process=False):
        super(RootPluginManager, self).__init__()
        self.enabled = {}
        self.__init_process_synchronization(multi_process)
        self.__init_must_enable()
    
    def __init_must_enable(self):
        """
        Registers and enables plugins configured as core plugins.  core plugins
        provide functionality required for the application to run
        """
        #package in tuple for compatibility
        enable = settings.CORE_PLUGINS
        if not isinstance(settings.CORE_PLUGINS, (list, tuple)):
            enable = (enable,)
        #register & enable
        for class_ in enable:
            if isinstance(class_, (str,)):
                # convert string into class
                last_dot = class_.rfind('.')
                from_ = class_[:last_dot]
                name = class_[last_dot+1:]
                class_ = __import__(from_, {}, {}, [name]).__dict__[name]
            class_.core = True
            self.register(class_)
        map(self.enable, self.plugins.keys())

    def __init_process_synchronization(self, multi_process):
        """
        Initializes synchronization between multiple instances of this app.
        
        When deployed in a production environment, apache will often create
        one instance of the app per apache thread.  The different threads must
        synchronize configuration changes in a sane way.  RootPluginManager
        uses multiprocessing to synchronizes
        """
        self.owner = None
        self.owner_timeout = datetime.now()
        
        if not multi_process:
            # fall back to standard threading api
            self.lock = RLock()
            try:
                self.config = PluginConfig.objects.get(name='ROOT_MANAGER')
            except PluginConfig.DoesNotExist:
                self.config = PluginConfig()
                self.config.name = 'ROOT_MANAGER'
                self.config.save()
            return

        while not self.config:
            try:
                self.config = PluginConfig.objects.get(name='ROOT_MANAGER')
            except PluginConfig.DoesNotExist:
                # config doesn't exist, it's up to the sync manager to create
                # it.  Sleep until it has been created.
                time.sleep(1)
        SyncManager.register('get_enabled')
        SyncManager.register('get_lock')
        self.sync_manager = SyncManager(address=('', 61000), authkey='goaway123984')
        self.sync_manager.connect()
        self.enabled = self.sync_manager.get_enabled()
        self.lock = self.sync_manager.get_lock()


    def acquire(self, contender, timeout=15000):
        """
        acquires ownership of the manager, allowing configuration changes.
        
        @param contender - a string identifying the contender trying to acquire
        @param timeout - how long the owner will hold the lock
        """
        try:
            self.lock.acquire()
            if self.owner != contender and datetime.now() < self.owner_timeout:
                return False
            self.owner = contender
            self.owner_timeout=datetime.now() + timedelta(0,0,0,timeout)
            return True
        finally:
            self.lock.release()


    def release(self, contender):
        """
        Releases lock.  only the current owner may do this unless the lock has
        timed out
        """
        try:
            self.lock.acquire()
            if self.owner == contender or self.owner_timeout < datetime.now():
                self.owner = None
                self.owner_timeout = None
        finally:
            self.lock.release()
 
    def autodiscover(self):
        """
        Auto-discover INSTALLED_APPS plugins.py modules and fail silently when
        not present. This forces an import on them to register any tasks they
        may want.
        """
        import imp
        import inspect
        from django.conf import settings
        
        # the path someone imports is important.  import all the different
        # possibilities so we can check them all
        from maintain.core.plugins.plugin import Plugin as PluginA
        from core.plugins.plugin import Plugin as PluginB
        subclasses = (PluginA, PluginB)
        
        print '[info] RootPluginManager - Autodiscovering Plugins'

        for app in filter(lambda x: x!='core', settings.INSTALLED_APPS):
            print '[info] checking app: %s' % app
            # For each app, we need to look for an plugin.py inside that app's
            # package. We can't use os.path here -- recall that modules may be
            # imported different ways (think zip files) -- so we need to get
            # the app's __path__ and look for plugin.py on that path.

            # Step 1: find out the app's __path__ Import errors here will (and
            # should) bubble up, but a missing __path__ (which is legal, but
            # weird) fails silently -- apps that do weird things with __path__
            # might need to roll their own plugin registration.
            try:
                app_path = __import__(app, {},{}, [app.split('.')[-1]]).__path__
            except AttributeError:
                continue

            # Step 2: use imp.find_module to find the app's plugin.py. For some
            # reason imp.find_module raises ImportError if the app can't be found
            # but doesn't actually try to import the module. So skip this app if
            # its plugin.py doesn't exist
            try:
                imp.find_module('plugins', app_path)
            except ImportError:
                continue

            # Step 3: load all the plugins in the plugin file
            module = __import__("%s.plugins" % app, {}, {}, ['Plugin'])
            configs = []
            for key, plugin in module.__dict__.items():
                if type(plugin)==type and not plugin in subclasses:
                    if issubclass(plugin, subclasses):
                        configs.append(self.register(plugin))

            # Step 4: enable any plugins that were marked as enabled
            try:
                self.lock.acquire()
                for config in configs:
                    if config.enabled:
                        self.enable(config.name)
            finally:
                self.lock.release()

    def disable(self, name):
        """
        Disables a plugin, and any plugins that depend on it.
        
        @param name - name of plugin
        """
        with self.lock:
            if name not in self.enabled:
                return
            plugin = self.enabled[name]
            for depended_plugin in plugin.get_depended():
                self.__disable(depended_plugin)
            self.__disable(plugin)

    def __disable(self, plugin):
        """
        Private function for disabling a plugin.  disable() handles
        iteration to disable plugins thats depend on this one.  This function
        handles the actual steps to disable a plugin
        
        @param plugin - plugin instance to disable
        """
        del self.enabled[plugin.name()]
        config = PluginConfig.objects.get(name=plugin.name())
        config.enabled = False
        config.save()

    def enable(self, name):
        """
        Enables a plugin allowing it to register its objects and or plugins
        for existing objects.  This also enables all dependencies returned by
        get_depends(plugin).
        
        If the plugin or any depends fail to load then any enabled depends
        should be disabled.
        
        @param plugin - name of plugin to register
        @returns - Instance of plugin that was created/running, or None if it
        failed to load
        """
        try:
            self.lock.acquire()
            try:
                class_ = self.plugins[name]
            except KeyError:
                raise UnknownPluginException(name)
    
            # already enabled
            if name in self.enabled.keys():
                return self.enabled[name]
    
            # as long as get_depends() returns the list in order from eldest to
            # youngest, we can just iterate the list making sure each one is enabled
            # if they all succeed then the plugin can also be enabled.
            enabled = []
            try:
                for depend in class_.get_depends():
                    if depend.name() in self.enabled:
                        continue
                    depend_plugin = self.__enable(depend)
                    enabled.append(depend.name())
                plugin = self.__enable(class_)
            except Exception, e:
                #exception occured, rollback any enabled plugins in reverse order
                import traceback, sys
                print e
                type, value, traceback_ = sys.exc_info()
                traceback.print_tb(traceback_, limit=10, file=sys.stdout)
                if enabled:
                    enabled.reverse()
                    map(self.disable, enabled)
                raise e
            return plugin
        finally:
            self.lock.release()
        print '[info] enabled: %s' % name

    def __enable(self, class_):
        """
        Private function for enabling plugins.  Enable_plugin handles iteration
        of dependencies.  This function handles the actual steps for enabling
        an individual plugin
        
        @param class_ - plugin class to enable
        """
        print '[info] enabling: %s' % class_
        config = PluginConfig.objects.get(name=class_.name())
        plugin = class_(self, config)
        
        # register objects
        if isinstance(class_.objects, (list, tuple)):
            map(self.__register_object, class_.objects)
        else:
            self.__register_object(class_.objects)
        
        self.enabled[class_.name()] = plugin
        config.enabled = True
        config.save()
        return plugin
    
    def __register_object(self, obj):
        """
        Registers an object with a manager.  Registered objects are then
        accessible for use, or to register other objects with.
        
        an example of this is registering a PluginManager that manages Models
        or registering a Model with the ModelManager.
        
        @param obj - instance of Registerable or a known type that has been
        given a shortcut for easier registration.
        
        known types: models.Model
        """
        if not isinstance(obj, Registerable):
            try:
                found = False
                for name, object_type in self['TypeManager'].plugins.items():
                    if object_type.class_ == obj.__class__:
                        obj = object_type.wrapper(obj)
                        found = True
                        break
                if not found:
                    raise Exception('Class is not registerable: %s' % obj.__name__)
            except KeyError:
                raise Exception('Class is not registerable: %s' % obj.__name__)
        manager = self[obj._target]
        manager.register(obj)

    def register(self, class_):
        """
        Overridden to setup configuration
        
        @param class_ - Plugin class to register
        """
        try:
            self.lock.acquire()
            super(RootPluginManager, self).register(class_)
            try:
                config = PluginConfig.objects.get(name=class_.name())
            except PluginConfig.DoesNotExist:
                config = PluginConfig()
                config.name = class_.name()
                config.set_defaults(class_.config_form)
                config.save()
            return config
        finally:
            self.lock.release()
    
    def update_config(self, name, config):
        """
        Updates the config for a plugin.  Changes are commited to the database
        and if the plugin is enabled, it is reloaded with the new config
        
        @param name - name of plugin to update
        @param config - PluginConfig to reload it with
        """
        config.save()
        with self.lock:
            if plugin in self.enabled:
                plugin = self.enabled[name]
                plugin.update_config(config)