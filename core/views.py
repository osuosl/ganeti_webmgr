from datetime import datetime
import simplejson
import sys
import traceback

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.text import capfirst

from plugins import RootPluginManager, get_depends, get_depended, \
                    CyclicDependencyException
from models import PluginConfig, SQLLock
from util.list_file import ListFile
import settings

# create a global manager that all views will use
manager = RootPluginManager()
manager.autodiscover()


def settings_processor(request):
    """
    settings_processor adds settings required by most pages
    """
    return {
        'VERSION':settings.VERSION,
        'MEDIA':settings.MEDIA_URL,
        'ROOT':settings.ROOT_URL
    }

def requires_config_lock(fn):
    """
    decorator for adding config lock to handlers
    """
    def new(request, *args, **kwargs):
        print 'requires ======================='
        try:
            active_lock = request.session['CONFIG_ACTIVE_LOCK']
            timeout_lock = request.session['CONFIG_TIMEOUT_LOCK']
            print active_lock, timeout_lock
        except KeyError:
            print 'NEW LOCKS'
            active_lock = SQLLock()
            timeout_lock = SQLLock()
        request.session['CONFIG_ACTIVE_LOCK'] = active_lock
        request.session['CONFIG_TIMEOUT_LOCK'] = timeout_lock
        if active_lock.acquire('CONFIG_ACTIVE_LOCK', 15000):
            print 'acquired active lock', active_lock.id
            timeout_lock.acquire('CONFIG_TIMEOUT_LOCK',60000)
            print 'timeout lock', timeout_lock.id
        print '----------------------------------'
        return fn(request, *args, **kwargs)

    return new


@requires_config_lock
def plugins(request):
    """
    Renders configuration page for plugins
    """
    global manager
    c = RequestContext(request, processors=[settings_processor])
    
    plugins = [manager.plugins[k] for k in sorted(manager.plugins.keys())]
    return render_to_response('plugins.html',
            {'plugins': plugins, 'None':None}, \
            context_instance=c)


@requires_config_lock
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
                    for p in filter(expression, get_depends(plugin))]
        return HttpResponse(simplejson.dumps(plugins))
    except CyclicDependencyException, e:
        error = 'Plugin has a dependency cycle with: %s' % e
        return HttpResponse(simplejson.dumps([-1, error]))


@requires_config_lock
def dependeds(request):
    """
    returns a list of dependeds for a plugin
    """
    global manager
    name = request.GET['name']
    dependeds = get_depended(manager.enabled[name])
    plugins = [{'name':p.name, 'description':p.description} for p in dependeds]
    return HttpResponse(simplejson.dumps(plugins))


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
    enabled = [p.__name__ for p in filter(expression, get_depends(plugin))]
    enabled.append(name)

    try:
        if manager.enable(name):
            return HttpResponse(simplejson.dumps(enabled))
    except Exception, e:
        error = ['Exception enabling plugin or one of its dependencies']
        return HttpResponse(simplejson.dumps([-1, error]))


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
    disabled = [p.name for p in get_depended(plugin)]
    disabled.append(name)
    
    manager.disable(name)
    return HttpResponse(simplejson.dumps(disabled))


@requires_config_lock
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


def refresh_active_lock(request):
    """
    Part of a composite locking system.  ACTIVE_LOCK is used to determine if
    the user is currently on the page.  If the user leaves the page the
    ACTIVE_LOCK will expire in 15 seconds.
    
    The ACTIVE_LOCK should be refreshed before it expires to ensure that no 
    other contender ever obtains the lock while the user is still on the page.
    Obtaining the short lock overrides the TIMEOUT_LOCK.
    
    The TIMEOUT_LOCK times the user out if there are no edits after 5 minutes.
    If the TIMEOUT_LOCK expires then the ACTIVE_LOCK is removed.  This allows
    users who leave the browser window open to time out.
    """
    active_lock = request.session['CONFIG_ACTIVE_LOCK']
    timeout_lock = request.session['CONFIG_TIMEOUT_LOCK']
    request.session['CONFIG_ACTIVE_LOCK'] = active_lock
    request.session['CONFIG_TIMEOUT_LOCK'] = timeout_lock
    
    print 'starting lock', active_lock.id, timeout_lock.id, timeout_lock.release_time
    
    if active_lock.acquired and datetime.now() > timeout_lock.release_time:
        # CONFIG_TIMEOUT_LOCK expired, send signal to stop ACTIVE_LOCK
        # contention.  This allows the lock to be acquired by someone else
        active_lock.release()
        timeout_lock.release()
        return HttpResponse(-2)
    
    acquired = active_lock.acquire('CONFIG_ACTIVE_LOCK', 15000)
    print 'refresh active lock', active_lock.id, acquired
    if acquired:
        if not timeout_lock.acquired:
            # only acquire CONFIG_TIMEOUT_LOCK if it is not already held.  This
            # allows another user to acquire the lock from a timeout
            timeout_lock.acquire('CONFIG_TIMEOUT_LOCK',180000)
        return HttpResponse(1)
    return HttpResponse(-1)