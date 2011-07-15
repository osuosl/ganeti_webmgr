from tastypie.http import HttpApplicationError

__author__ = 'bojan'

from tastypie.models import ApiKey
from django.http import HttpResponse
from tastypie.bundle import Bundle
from django.core.context_processors import request
import api.resources


def generate_api_key(request, userid):
    api_key = None
    try:
        api_key = ApiKey.objects.get(user=userid)
        api_key.key = api_key.generate_key()
        api_key.save()
    except ApiKey.DoesNotExist:
        api_key = ApiKey.objects.create(user=userid)

    # return created key info
    if (api_key != None):
        bun = Bundle()
        bun.data['userid'] = userid
        bun.data['api_key'] = api_key.key
        ur = api.resources.UserResource()
        return HttpResponse(status=201, content=ur.serialize(request, bun, ur.determine_format(request)))

def clean_api_key(request, userid):
    api_key = None
    try:
        api_key = ApiKey.objects.get(user=userid)
        api_key.delete()
    except ApiKey.DoesNotExist:
        api_key = None
    if (not api_key):
        return HttpResponse(status=201)
    else:
        return HttpApplicationError
    
