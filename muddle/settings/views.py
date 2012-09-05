import cPickle
import simplejson

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from muddle.settings.models import AppSettingsValue, AppSettingsCategory
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
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    subcategories = {}
    for name, klass in SETTINGS[category].items():
        full_name = '%s.%s' % (category, name)
        values = AppSettingsValue.objects.filter(category__name=full_name) \
            .values_list('key','serialized_data')
        values_dict = {}
        for k, v in values:
            values_dict[k]=cPickle.loads(str(v))
        subcategories[name] = klass(values_dict)

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
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    klass = SETTINGS[category][subcategory]
    form = klass(request.POST)

    full_name = '%s.%s' % (category, subcategory)
    category_instance, new = AppSettingsCategory.objects.get_or_create(name=full_name)
    if form.is_valid():
        data = form.cleaned_data
        for field in form.base_fields.keys():
            if field in data and data[field] != '':
                try:
                    value = AppSettingsValue.objects.get(category=category_instance, key=field)
                except AppSettingsValue.DoesNotExist:
                    value = AppSettingsValue(category=category_instance, key=field)
                value.data = data[field]
                value.save()
            else:
                # delete fields that were not passed in.
                try:
                    AppSettingsValue.objects\
                        .get(category=category_instance, key=field) \
                        .delete()
                except AppSettingsValue.DoesNotExist:
                    # Don't need to delete a value that doesn't exist
                    pass

        return HttpResponse("1",  mimetype="application/json")
    
    return HttpResponse(simplejson.dumps(form.errors), mimetype="application/json")