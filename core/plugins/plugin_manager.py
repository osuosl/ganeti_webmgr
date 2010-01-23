from datetime import datetime, timedelta
from threading import RLock
from multiprocessing.managers import SyncManager

from core.models import PluginConfig
from plugin import get_depended, get_depends, Plugin
from core.plugins import CyclicDependencyException, UnknownPluginException

class PluginManager(object):
    """
    Manages the lifecycle of plugins.  Plugins may be registered making the
    manager awar of the plugin.  The plugins may then be enabled or disabled.
    """
    def __init__(self):
        self.plugins = {}

    def register(self, class_):
        """
        Registers a plugin with this manager.  Plugins are stored by __name__
        so that they may be looked up later.  Registration just makes them
        available to use on this installation, they don't add any functionality
        or check dependencies until they are enabled with enable_plugin()
        
        @param class_ - plugin class to register
        """
        print '[Info] Registering: ', class_.__name__
        self.plugins[class_.__name__] = class_

    def registers(self, classes):
        """
        Registers a collection of plugins
        @param classes - iterable of plugin Classes
        """
        for class_ in classes:
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
        from maintain.core.plugins import Plugin as PluginA
        from core.plugins import Plugin as PluginB
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
            # its tasks.py doesn't exist
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
            for depended_plugin in get_depended(plugin):
                self.__disable(depended_plugin)
            self.__disable(plugin)

    def __disable(self, plugin):
        """
        Private function for disabling a plugin.  disable() handles
        iteration to disable plugins thats depend on this one.  This function
        handles the actual steps to disable a plugin
        
        @param plugin - plugin instance to disable
        """
        del self.enabled[plugin.name]
        config = PluginConfig.objects.get(name=plugin.name)
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
            if name in self.enabled.items():
                return self.enabled[name]
    
            # as long as get_depends() returns the list in order from eldest to
            # youngest, we can just iterate the list making sure each one is enabled
            # if they all succeed then the plugin can also be enabled.
            enabled = []
            try:
                for depend in get_depends(class_):
                    if depend.__name__ in self.enabled:
                        continue
                    depend_plugin = self.__enable(depend)
                    enabled.append(depend.__name__)
                plugin = self.__enable(class_)
            except Exception, e:
                #exception occured, rollback any enabled plugins in reverse order
                if enabled:
                    enabled.reverse()
                    for plugin in enabled:
                        self.disable(plugin)
                raise e
            return plugin
        finally:
            self.lock.release()


    def __enable(self, class_):
        """
        Private function for enabling plugins.  Enable_plugin handles iteration
        of dependencies.  This function handles the actual steps for enabling
        an individual plugin
        
        @param class_ - plugin class to enable
        """
        config = PluginConfig.objects.get(name=class_.__name__)
        plugin = class_(self, config)
        self.enabled[class_.__name__] = plugin
        config.enabled = True
        config.save()
        return plugin

    def register(self, class_):
        """
        Overridden to setup configuration
        
        @param class_ - Plugin class to register
        """
        try:
            self.lock.acquire()
            super(RootPluginManager, self).register(class_)
            try:
                config = PluginConfig.objects.get(name=class_.__name__)
            except PluginConfig.DoesNotExist:
                config = PluginConfig()
                config.name = class_.__name__
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