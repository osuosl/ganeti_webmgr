from core.plugins.plugin_manager import PluginManager
from core.plugins.plugin import Plugin
from core.plugins.registerable import Registerable

class ObjectType(Registerable):
    """
    Maps a type to a wrapper class.
    """
    target = 'TypeManager'
    _target = 'TypeManager'
    
    def __init__(self, class_, wrapper):
        self.class_ = class_
        self.wrapper = wrapper
    
    def name(self):
        return self.class_.__name__


class TypeManager(Plugin, PluginManager):
    """
    Manager that registers ObjectTypes for ease registering object types 
    """
    description = 'Manager that registers ObjectTypes for ease registering object types'
    
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        PluginManager.__init__(self)