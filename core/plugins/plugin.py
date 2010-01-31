from core.plugins import CyclicDependencyException
from core.plugins.registerable import Registerable

class Plugin(Registerable):
    """
    A Plugin is something that provides new functionality to PROJECT_NAME.  A
    plugin may register various objects such as Models, Views, and Processes
    or register plugins to existing objects.
    
    A Plugin is used when the ability to enable and disable plugins is needed.
    Plugins contains other Registerable objects that are registered with other
    Managers.
    """
    manager = None
    depends = None
    description = 'I am a plugin who has not been described'
    config_form = None
    objects = ()
    core = False
    
    def __init__(self, manager, plugin_config):
        """
        Creates the plugin.  Does *NOT* initialize the plugin.  This should only
        set configuration.

        @param manager - PluginManager that this plugin is enabled with
        @param plugin_config - PluginConfig corresponding with this class
        """
        self.manager = manager
        self.update_config(plugin_config)

    @classmethod
    def _deregister(self, manager):
        """
        overloaded to move to a classmethod.
        """
        pass

    @classmethod
    def _register(self, manager):
        """
        overloaded to move to a classmethod.
        """
        pass

    def update_config(self, plugin_config):
        """
        Updates configuration.  By default this unpacks PluginConfig.config to
        self.__dict__
        
        @param plugin_config - PluginConfig corresponding with this class
        """
        reserved_names = ('manager','description','depends','enabled')
        self.is_enabled = plugin_config.enabled
        if plugin_config.config:
            for key, value in plugin_config.config.items():
                if key in reserved_names:
                    raise Exception('Attempted to set reserved property (%s)' +\
                                    'via config') % (key)
                self.__dict__[key] = value

    def get_depended(self):
        """
        Gets a list of enabled plugins that depend on this plugin.  This looks up
        the depends of all active plugins searching for this plugin.  It also does
        a recursive search of any depended that is found.
        
        This differs from get_depends() in that it works with instances of the
        plugin rather than the class.  We're only concerned about depended plugins
        when they are enabled.
        
        the list returns sorted in order that removes all depended classes before
        their dependencies
        
        @param self - an enabled Plugin
        @returns list of Plugins
        """
        def add(value, set):
            """Helper Function for set-like lists"""
            if value not in set:
                set.append(value)
                
        #initial checks
        if not self.manager:
            return None
        
        #build depended list
        class_ = self.__class__
        depended = []
        for name, enabled in self.manager.enabled.items():
            if class_ in enabled.get_depends():
                add(enabled, depended)
        depended.reverse()
        return depended

    @classmethod
    def get_depends(class_, descendents=set()):
        """
        Gets a list of dependencies for this plugin class, including recursive
        dependencies.  Dependencies will be sorted in order in which they need to
        be loaded
        
        @param class_ - class to get depends for
        @param descendents - child classes that are requesting depends for a parent.
        Used to check for cyclic dependency errors.
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
            grandparents = parent.get_depends(descendents_)
            if grandparents:
                for grandparent in grandparents:
                    add(grandparent, _depends)
            add(parent, _depends)
            
        return _depends
