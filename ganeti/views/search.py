import json
from haystack.query import SearchQuerySet as searchset

def results(request):
    '''
    Return search results as a JSON object.
    '''

    

    return HttpResponse('{}', mimetype='application/json')
