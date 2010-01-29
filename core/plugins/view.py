from core.plugins.registerable import Registerable

class View(Registerable):
    """
    Base class for views that can be registered.
    """
    url = None
    handler = None
    target = 'ViewHandler'
    _target = 'ViewHandler'
    
    def __init__(self, url, handler):
        """
        @param url - regex url pattern
        @param handler - function that will process the request
        """
        self.url = url
        self.handler = handler