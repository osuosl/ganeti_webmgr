import re

from django.shortcuts import render_to_response
from django.template import RequestContext

from muddle import settings_processor
from muddle.plugins.plugin import Plugin
from muddle.plugins.managers.plugin_manager import PluginManager


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
                return plugin(request, *match.groups())
            
        c = RequestContext(request, processors=[settings_processor])
        return render_to_response('errors/404.html', context_instance=c)

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