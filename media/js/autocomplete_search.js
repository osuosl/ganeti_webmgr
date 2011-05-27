/* JavaScript responsible for making the autocomplete search box work. */

var autocomplete_search = function(search_box, search_form, autocomplete_lib){
    /* Customized autocomplete search box for use with GWM's search system.
     *
     * This autocomplete search box works with the search.py view to provide
     * a list of search suggestions.
     *
     * `search_box` is a jQuery object representing the search input box
     * `search_form` is a jQuery object that represents the search form that
     *      houses the `search_box`
     *
     *  Requires jQuery and jquery-ui (with the autocomplete widget)
     */

    // keycode for the enter/return key
    var ENTER_KEYCODE = 13;

    $(function(){
        /* "Main" */
        
        var autocomplete = autocomplete_lib;

        // Autocomplete search box
        search_box.autocomplete({
            source: "{% url search-json %}",
            //source: example_results, 
            minLength: 2,

            // Custom focus function to handle our custom results format
            focus: function( event, ui ) {
                search_box.val(ui.item.value);
                return false;
            },

            // Submit the search on item selection
            select: function(){
                search_form.submit();
            }
        })

        // Submit search on return/enter keypress
        .keydown(function(event){
            if(event.keyCode == ENTER_KEYCODE){
                search_form.submit();
            }
        })

        // Create custom result item rendering for out custom format
        .data("autocomplete")._renderItem = function(ul, item){
            return $("<li></li>")
                .data("item.autocomplete", item)
                .append("<a><b>" + item.type + ": </b>" + item.value + "</a>")
                .appendTo(ul);
        };

        // Remove the widget-content class b/c it is customized for tab use in
        // other parts of the site.  We'll customize the the autocomplete box
        // in the styles above.
        $('.ui-autocomplete').removeClass('ui-widget-content');
    });
}
