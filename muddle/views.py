from datetime import datetime
import simplejson
import sys
import traceback

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.text import capfirst

from muddle import settings_processor
from plugins import CyclicDependencyException
from plugins.managers.root_plugin_manager import RootPluginManager
from models import PluginConfig, SQLLock
from util.list_file import ListFile
import settings

# create a global manager that all views will use
manager = RootPluginManager()
manager.autodiscover()


def requires_config_lock(fn):
    """
    decorator for adding config lock to handlers
    """
    def new(request, *args, **kwargs):
        global manager
        if manager.acquire(request.session._session_key):
            return fn(request, *args, **kwargs)
        else:
            return HttpResponse(simplejson.dumps([-1,'No Lock']))

    return new

@user_passes_test(lambda u: u.has_perm('muddle.change_pluginconfig'))
def plugins(request):
    """
    Renders configuration page for plugins
    """
    global manager
    c = RequestContext(request, processors=[settings_processor])
    
    plugins = [manager.plugins[k] for k in sorted(manager.plugins.keys())]
    return render_to_response('plugins.html',
            {'plugins': plugins}, \
            context_instance=c)


def depends(request):
    """
    returns a list of depends for a plugin
    """
    global manager
    name = request.GET['name']
    expression = lambda x: not x.__name__ in manager.enabled
    plugin = manager.plugins[name]
    try:
        plugins = [{'name':p.__name__, 'description':p.description} \
                    for p in filter(expression, plugin.get_depends())]
        return HttpResponse(simplejson.dumps(plugins))
    except CyclicDependencyException, e:
        error = 'Plugin has a dependency cycle with: %s' % e
        return HttpResponse(simplejson.dumps([-1, error]))


def dependeds(request):
    """
    returns a list of dependeds for a plugin
    """
    global manager
    name = request.GET['name']
    dependeds = manager.enabled[name].get_depended()
    plugins = [{'name':p.name, 'description':p.description} for p in dependeds]
    return HttpResponse(simplejson.dumps(plugins))


@user_passes_test(lambda u: u.has_perm('muddle.change_pluginconfig'))
@requires_config_lock
def enable(request):
    """
    Enables a plugin and any of its dependencies
    
    @returns list of newly enabled plugins, or list of errors if fails
    """
    global manager
    name = request.GET['name']

    # create list of newly enabled plugins. Must do this before they are enabled
    # else there is no way to determine which ones weren't active beforehand
    expression = lambda x: not x.__name__ in manager.enabled
    plugin = manager.plugins[name]
    enabled = [p.__name__ for p in filter(expression, plugin.get_depends())]
    enabled.append(name)

    try:
        if manager.enable(name):
            return HttpResponse(simplejson.dumps(enabled))
    except Exception, e:
        error = ['Exception enabling plugin or one of its dependencies']
        return HttpResponse(simplejson.dumps([-1, error]))


@user_passes_test(lambda u: u.has_perm('muddle.change_pluginconfig'))
@requires_config_lock
def disable(request):
    """
    Disables a plugin and any that depend on it
    """
    global manager
    name = request.GET['name']
    
    # get list of newly diabled plugins. Must do this before they are disabled
    # else there is no way to determine which ones weren't active beforehand
    plugin = manager.enable(name)
    disabled = [p.name for p in plugin.get_depended()]
    disabled.append(name)
    
    manager.disable(name)
    return HttpResponse(simplejson.dumps(disabled))


@user_passes_test(lambda u: u.has_perm('muddle.change_pluginconfig'))
def config(request, name):
    """
    Config edit page for plugins.  This is a generic handler that deals with
    the django form class stored in plugin.config_form.  This includes both
    plugins with a single config form, and plugins with multiple forms
    
    @request HttpRequest - request object sent by django
    @param name - name of plugin to configure
    """
    global manager
    form_class = manager.plugins[name].config_form
    plugin_config = PluginConfig.objects.get(name=name)
    if isinstance(form_class, (list, tuple)):
        forms = []
        for class_ in form_class:
            form = class_(plugin_config.config)
            if not 'name' in class_.__dict__:
                form.name = class_.__name__
            form.class_ = class_.__name__
            forms.append(form)
        return render_to_response('config_tabbed.html', \
                                  {'name':name, 'forms':forms})
    else:
        form = form_class(plugin_config.config)
        return render_to_response('config.html', {'name':name, 'form':form})


@user_passes_test(lambda u: u.has_perm('muddle.plugins_config'))
@requires_config_lock
def config_save(request, name):
    """
    Generic handler for saving configuration.  This handler deals with plugins
    that have a single form, or multiple forms
    
    @request HttpRequest - request object sent by django
    @param name - name of plugin to configure
    """
    global manager
    form_class = manager.plugins[name].config_form
    plugin_config = PluginConfig.objects.get(name=name)
    if isinstance(form_class, (list, tuple)):
        tab = request.POST['tab']
        for class_ in form_class:
            if class_.__name__ == tab:
                form_class = class_
                break
    form = form_class(request.POST)
    if form.is_valid():
        for k, v in form.cleaned_data.items():
            if k == 'tab':
                continue
            plugin_config.config[k] = v
        plugin_config.save()
        return HttpResponse(1)
    errors = []
    for k, v in form.errors.items():
        for error in v:
            errors.append([capfirst(k), error._proxy____args[0]])
    return HttpResponse(simplejson.dumps(errors))


def acquire_lock(request):
    """
    Acquires a lock.  should be called by clients that wish to obtain the lock
    This method is different from refresh_lock() in that it is safe to cache.
    The cache will only be released after 15 seconds.  Prior to this all users
    will receive the same message.
    
    When the lock is open, this function cannot be cached otherwise multiple
    users would think they received the lock, when they just received a response
    indicating they received it.
    
    If multiprocess is being used for synchronization, caching here is
    especially important.  Acquiring the lock involves communicating through
    an external interface, possibly across the network.  allowing many requests
    to fight over the lock just to check the timeout status is a major
    bottleneck.
    """
    cached = cache.get('REFRESH_LOCK')
    if cached:
        return cached
    
    # create and cache the fail response.  Only one person will get the lock so
    # if one user has gotten past the cache, then the next user is already too
    # late to get the lock anyways
    fail_response = HttpResponse(-1)
    cache.set('REFRESH_LOCK', fail_response, 14)
    
    if manager.acquire(request.session._session_key):
        return HttpResponse(1)
    return fail_response


def refresh_lock(request):
    """
    used by the holder of the lock to refresh the timeout proving they are still
    active.
    
    This method must never be cached.  while the result should almost
    always be the same, manager.acquire() must be hit to ensure the timeout is
    bumped.  Caching here isn't needed because very few users should be hitting
    this at any given time.
    
    This method should be called more frequently than the lock timeout.  IE.  if
    the lock times out in 15 seconds, this method should be called <14 seconds.
    Take into account latency times of the network, this affects both the HTTP
    request, and the time for acquiring the lock that must be held to modify the
    timestamp.
    """
    if manager.acquire(request.session._session_key):
        return HttpResponse(1)
    return HttpResponse(-1)
    
  
def release_lock(request):
    """
    Used by the holder of the lock to release it.  This can be used to
    explicitly release a lock.  In most cases this isn't needed because a lock
    will timeout automatically due to inactivity.
    """
    manager.release(request.session._session_key)
    
    
    