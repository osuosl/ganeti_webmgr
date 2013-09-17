from haystack.query import SearchQuerySet

from django.contrib.auth.decorators import login_required
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseNotFound)
from django.utils import simplejson as json

from virtualmachines.models import VirtualMachine
from clusters.models import Cluster
from nodes.models import Node


@login_required
def suggestions(request):
    ''' Return a list of search results for the autocomplete search box.

    Return a list of search results for the query in the GET parameter `term`
    as a JSON object. If `term` does not exist, just return a blank list.

    The format consists of a list of objects representing the object name and
    the object type. Here's an example:

        [
            {
                'value':    'foo',
                'type':     'vm',
            },
            {
                'value':    'bar',
                'type':     'vm',
            },
            {
                'value':    'herp',
                'type':     'cluster',
            },
            {
                'value':    'derp',
                'type':     'node',
            }
        ]
    '''
    # Get the query from the GET param
    query = request.GET.get('term', None)

    # Start out with an empty result objects list
    result_objects = []

    # If a query actually does exist, construct the result objects
    if query is not None:

        # Perform the actual query on the Haystack search query set
        results = SearchQuerySet().autocomplete(content_auto=query)

        # Construct the result objects
        for result in results:
            result_object = {}
            result_object['value'] = result.content_auto
            if result.model_name == 'virtualmachine':
                result_object['type'] = 'vm'
            elif result.model_name == 'cluster':
                result_object['type'] = 'cluster'
            elif result.model_name == 'node':
                result_object['type'] = 'node'
            else:
                result_object['type'] = 'unknown'
            result_objects.append(result_object)

    # Return the results list as a json object
    return HttpResponse(json.dumps(result_objects, indent=4),
                        mimetype='application/json')


@login_required
def detail_lookup(request):
    '''
    Look up and redirect to the detail page for the given object.

    There must be two supplied GET parameters:
        `type`:     which declares the type of object we're looking up, and
                    the possible values should be either 'vm', 'cluster', or
                    'node'.
        `hostname`: Hostname of the object.
    '''
    # Grab the GET parameters
    object_type = request.GET.get('type', None)
    hostname = request.GET.get('hostname', None)

    # Variable for the queried object
    obj = None

    # Try getting the object, 404 if it can't be found
    try:

        # If the object type is a vm or node, we need to select the related
        # cluster so we don't make an additional db query
        if object_type == 'vm':
            obj = VirtualMachine.objects.filter(hostname=hostname)\
                .select_related('cluster')[0]
        elif object_type == 'node':
            obj = Node.objects.filter(hostname=hostname)\
                .select_related('cluster')[0]
        elif object_type == 'cluster':
            obj = Cluster.objects.filter(hostname=hostname)[0]
        else:
            return HttpResponseNotFound()
    except IndexError:
        return HttpResponseNotFound()

    # Redirect to the absolute URL of the object
    return HttpResponseRedirect(obj.get_absolute_url())
