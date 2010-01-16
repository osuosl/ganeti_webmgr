import simplejson

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from plugins import RootPluginManager, get_depends, get_depended
from models import PluginConfig

# create a global manager that all views will use
manager = RootPluginManager()
manager.autodiscover()


def plugins(request):
    """
    Renders configuration page for plugins
    """
    global manager
    
    return render_to_response('plugins.html',
            {'plugins': PluginConfig.objects.all()})


def depends(request):
    """
    returns a list of depends for a plugin
    """
    global manager
    name = request.GET['name']
    expression = lambda x: not x.__name__ in manager.enabled
    plugin = manager.plugins[name]
    plugins = [{'name':p.__name__, 'description':p.description} \
                    for p in filter(expression, get_depends(plugin))]
    return HttpResponse(simplejson.dumps(plugins))


def dependeds(request):
    """
    returns a list of dependeds for a plugin
    """
    global manager
    name = request.GET['name']
    dependeds = get_depended(manager.enabled[name])
    plugins = [{'name':p.name, 'description':p.description} for p in dependeds]
    return HttpResponse(simplejson.dumps(plugins))
    
    
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
    enabled = [p.__name__ for p in filter(expression, get_depends(plugin))]
    enabled.append(name)

    if manager.enable(name):
        return HttpResponse(simplejson.dumps(enabled))
    return HttpResponse(-1)


def disable(request):
    """
    Disables a plugin and any that depend on it
    """
    global manager
    name = request.GET['name']
    
    # get list of newly diabled plugins. Must do this before they are disabled
    # else there is no way to determine which ones weren't active beforehand
    plugin = manager.enable(name)
    disabled = [p.name for p in get_depended(plugin)]
    disabled.append(name)
    
    manager.disable(name)
    return HttpResponse(simplejson.dumps(disabled))