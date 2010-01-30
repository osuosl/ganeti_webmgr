from core.plugins.plugin_manager import PluginManager
from core.plugins.plugin import Plugin


class ViewManager(Plugin, PluginManager):
    """
    Manager that registers views and exposes their URLs to django's view system 
    """
    description = 'Manager that registers views and exposes their URLs to django''s view system'
    
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        PluginManager.__init__(self)