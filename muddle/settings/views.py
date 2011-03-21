import simplejson
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from muddle.settings.registration import SETTINGS


@login_required
def index(request):
    """
    base view for settings
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    return render_to_response('muddle/settings/categories.html',
        {'categories':SETTINGS},
        context_instance=RequestContext(request))


@login_required
def detail(request, category):
    """
    View for displaying a category detail.  This is will render a view with all
    subcategories available.
    """
    subcategories = {}
    for name, klass in SETTINGS[category].items():
        
        subcategories[name] = klass()
        print subcategories[name]

    return render_to_response('muddle/settings/detail.html',
        {
            'category':category,
            'forms':subcategories
        },
        context_instance=RequestContext(request))


@login_required
def save(request, category, subcategory):
    """
    View for saving settings.  This will save settings for a single category
    """

    if request.method != 'POST':
        return HttpResponseNotAllowed()

    klass = SETTINGS[category][subcategory]
    form = klass(request.POST)

    if form.is_valid():
        return HttpResponse("1")
    
    return HttpResponse(simplejson.dumps(form.errors), mimetype="application/json")