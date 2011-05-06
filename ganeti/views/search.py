import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from haystack.query import SearchQuerySet

@login_required
def search_json(request):
    '''
    Return a list of search results for the query in the GET parameter `term` 
    as a JSON object. If `term` does not exist, just return a blank list.
    '''
    query = request.GET.get('term', None)

    if query is not None:
        results = SearchQuerySet().autocomplete(content_auto=query)
        results_list = [result.content_auto for result in results]
        results_json = json.dumps(results_list, indent=4)
    else:
        results_json = json.dumps([])

    return HttpResponse(results_json, mimetype='application/json')

