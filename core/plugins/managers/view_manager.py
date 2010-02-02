import re

from django.http import HttpResponse

from core.plugins.plugin_manager import PluginManager
from core.plugins.plugin import Plugin


class ViewManager(Plugin, PluginManager):
    """
    Manager that registers views and exposes their URLs to django's view system
    
    Views that are registered with this manager will be exposed by a generic
    view handler.
    """
    description = 'Manager that registers views and exposes their URLs to django''s view system'
    
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        PluginManager.__init__(self)
        self.urls = {}

    def process(self, request, path):
        """
        Generic view handler that dispatches requests to registered views.
        
        @param request - HttpRequest 
        @param path - path requested
        """
        for regex, plugin in self.urls.items():
            match = regex.match(path)
            if match:
                return plugin(request, match.groups())
        
        return HttpResponse('redirect to 404')

    def register(self, plugin):
        """
        Overridden to setup regex url mappings for views
        """
        super(ViewManager, self).register(plugin)
        regex = plugin.regex
        if regex:
            if plugin.regex.__class__ == str:
                regex = re.compile(regex)
        else:
            regex = re.compile(plugin.name())
        self.urls[regex] = plugin