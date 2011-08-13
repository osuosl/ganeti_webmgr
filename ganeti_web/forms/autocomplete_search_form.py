# Custom Haystack search form for autocomplete searches

from haystack.forms import SearchForm


class autocomplete_search_form(SearchForm):
    '''
    Custom Haystack search form for autocomplete searches. Important so that
    users can search for 'foo' and get 'foo.bar', 'foo.bar.herp', etc.
    '''
    def search(self):
        '''
        Overwriting SearchForm's default search to implement autocomplete
        searching.
        '''
        if not self.is_valid():
            return self.no_query_found()

        if not self.cleaned_data.get('q'):
            return self.no_query_found()

        # Perform an autocomplete search query on the 'content_auto' fields of
        # the searchable models
        sqs = self.searchqueryset.autocomplete(content_auto=self.cleaned_data['q'])

        if self.load_all:
            sqs = sqs.load_all()

        return sqs
