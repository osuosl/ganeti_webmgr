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
        
    def __call__(self, request):
        """
        Views themselves are callable, though they generally will delegate work
        to the handler function after it has authorized the user.
        
        @param request - HttpRequest
        """
        if self.is_authorized(request.user.getProfile()):
            return self.handler(request)