from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from plugins import RootPluginManager

# create a global manager that all views will use
manager = RootPluginManager()
manager.autodiscover()


def plugins(request):
    """
    Renders page for plugins
    """
    global manager
    
    return render_to_response('plugins.html',
            {'manager': manager})