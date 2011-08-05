
__author__ = 'bojan'

from tastypie.http import HttpApplicationError, HttpBadRequest
from tastypie.serializers import Serializer
from tastypie.models import ApiKey
from tastypie.bundle import Bundle
import api.resources
from django.http import HttpRequest, HttpResponse

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
    
def serialize_and_reply(request, response, code = 200):
    if ('format=xml' in request.META['QUERY_STRING']):
        return HttpResponse(Serializer().serialize(response, format='application/xml'), content_type='application/xml', status = code)
    elif ("format=json" in request.META['QUERY_STRING']):
        return HttpResponse(content=Serializer().serialize(response, format='application/json'), content_type='application/json', status = code)
    elif ('application/json' in request.META['HTTP_ACCEPT']):
        return HttpResponse(content=Serializer().serialize(response, format='application/json'), content_type='application/json', status = code)
    elif ('application/xml' in request.META['HTTP_ACCEPT']):
        return HttpResponse(content=Serializer().serialize(response, format='application/xml'), content_type='application/xml', status= code)
    else:
        return HttpResponse(content="Please select either json or xml, in query or header", status=400)




def extract_log_actions(request, id, log):
    """
    Extracts log action items, links them to the related resources
    and return accordingly
    """
    # relation base class -> resource
    obj_res_instances = {'VirtualMachine': api.resources.VMResource, 'User': api.resources.UserResource, 'Group': api.resources.GroupResource, 'Cluster': api.resources.ClusterResource
                         , 'Node': api.resources.NodeResource, 'Job': api.resources.JobResource}
    glob_action_data = []
    
    # populate log with entries
    for entry in log:
        action_data = {}
        action_data.update({'action_name':entry.action.name})
        action_data.update({'user': api.resources.UserResource().get_resource_uri(entry.user)})
        action_data.update({'timestamp':entry.timestamp})

        try:
            if obj_res_instances.has_key(entry.object1.__class__.__name__):
                action_data.update({'obj1':obj_res_instances.get(entry.object1.__class__.__name__)().get_resource_uri(entry.object1)})
        except Exception:
            {}

        try:
            if obj_res_instances.has_key(entry.object2.__class__.__name__):
                action_data.update({'obj2':obj_res_instances.get(entry.object2.__class__.__name__)().get_resource_uri(entry.object2)})
        except Exception:
            {}

        try:
            if obj_res_instances.has_key(entry.object3.__class__.__name__):
                action_data.update({'obj3':obj_res_instances.get(entry.object3.__class__.__name__)().get_resource_uri(entry.object3)})
        except Exception:
            {}

        glob_action_data.append(action_data)
    return glob_action_data

def generate_wiki_basic_table(self, dict):
        print "|_. Name |_. Type | _. ReadOnly |_. Nullable |_. Description |_."
        for key in dict:
            ro = ""
            nl = ""
            if (dict[key].get('read_only')):
                ro = "x"
            else:
                ro = " "
            if (dict[key].get('nullable')):
                nl = "x"
            else:
                nl = " "
            print "|<code>" + key + "</code>|<code>" + dict[key]['type'] + "</code>|" + ro + "|" + nl + "|" + dict[key]['help_text'].__str__() + "|"
    