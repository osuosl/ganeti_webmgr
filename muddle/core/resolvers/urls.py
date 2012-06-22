from django.core.urlresolvers import reverse

__all__ = ['register','resolve']

_MODEL_URLS = {}
"""
Internal cache of registered urls
"""

def register(model, url, *args, **kwargs):
    """
    Register a detail url for models.  Registered urls can then be looked up
    with get_url(obj).
    
    @param model: model to register the url for
    @param url: url name that corresponds to the detail view
    @param args: list of properties that are needed for this url mapping. The
    values of these attributes will be passed to reverse() when constructing
    the url.
    @param kwargs: dict of attributes that will be passed as kwargs to reverse
    """
    if args and kwargs:
        raise ValueError("Don't mix args and kwargs in url mappings")
    elif not (args or kwargs):
        raise ValueError("requires args or kwargs")
    
    _MODEL_URLS[model] = (url, args, kwargs)


def smart_getattr(obj, attribute, default=AttributeError):
    """
    helper function that retrieves an attribute from a class.  This differs from
    getattr in that it will traverse through properties.
    
    e.g. smart_getattr('foo.bar.xoo', obj) will return obj.foo.bar.xoo
    """
    for attr_ in attribute.split('.'):
        if AttributeError == default:
            obj = getattr(obj, attr_)
        else:
            obj = getattr(obj, attr_, default)
    return obj


def resolve(obj):
    """
    Returns the detail url for the given object.  This method allows apps to
    provide contextual links for generic objects by using 
    django.core.urlresolvers.reverse()
    
    urls must first be registered with register(model, url, args)
    
    @param obj: a Model instance.
    """
    url, arg_names, kwarg_names = _MODEL_URLS[obj.__class__]
        
    # retrieve args from object
    if arg_names:
        args = [smart_getattr(obj, name) for name in arg_names]
        return reverse(url, args=args)
    
    # retrieve kwarg values from object
    kwargs = {}
    for kwarg, name in kwarg_names.items():
        kwargs[kwarg] = smart_getattr(obj, name)
    return reverse(url, kwargs=kwargs)
