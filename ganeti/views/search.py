import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from haystack.query import SearchQuerySet


@login_required
def search_json(request):
    ''' Return a list of search results for the autocomplete search box.

    Return a list of search results for the query in the GET parameter `term` 
    as a JSON object. If `term` does not exist, just return a blank list.

    The format consists of a list of objects representing the object name and 
    the object type. Here's an example:

        [
            {
                'value':    'foo',
                'type':     'vm',
                'url':      'vm/foo'
            },
            {
                'value':    'bar',
                'type':     'vm',
                'url':      'vm/bar'
            },
            {
                'value':    'herp',
                'type':     'cluster',
                'url':      'cluster/herp'
            },
            {
                'value':    'derp',
                'type':     'node',
                'url':      'node/derp'
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

            if hasattr(result.object, 'get_absolute_url'):
                result_object['url'] = result.object.get_absolute_url()
            result_objects.append(result_object)

    # Return the results list as a json object
    return HttpResponse(json.dumps(result_objects, indent=4), 
            mimetype='application/json')
    
