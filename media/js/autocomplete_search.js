/* JavaScript responsible for making the autocomplete search box work. */

function autocomplete_search(search_box, search_form, search_URL, lookup_URL){
    /* Customized autocomplete search box for use with GWM's search system.
     *
     * This autocomplete search box works with the search.py view to provide
     * a list of search suggestions as the user types. It must be provided the
     * following parameters:
     *
     *      `search_box`:   The search input box as a jQuery object
     *              e.g. $('#search_box')
     *      `search_form`:  The form that contains the search box as a jQuery
     *              object, e.g. $('#search_form')
     *      `search_URL`:   The url responsible for returning the search
     *              suggestions as a JSON object, e.g. 
     *              '/search-suggestions.json'
     *      `lookup_URL`:   The url responsible for returning the absolute URL
     *              to the details page for a GWM object
     *
     * Example markup:
     *      <form id='search_form' action='/search' method='GET'>
     *          <input id='search_box' type='text' name='q'>
     *      </form>
     *
     * Requires:
     *      jQuery and jquery-ui (with the autocomplete widget)
     */

    // keycode for the enter/return key
    var ENTER_KEYCODE = 13;
    
    // Submit search on return/enter keypress as long as no suggestion selected
    search_box.keydown(function(event){
        if(event.keyCode == ENTER_KEYCODE){
            if(!$('.ui-autocomplete #ui-active-menuitem').is(":visible")){
                search_form.submit();
            }
        }
    })
   
    // Initialize the autocomplete widget on the search box. This must go
    // *after* the keydown binding (above) in the chain so the autocomplete 
    // selection event takes precedence, i.e., when something is selected, go 
    // to its details page over simply searching for the keyword, and if
    // nothing's selected, search for the keyword.
    .autocomplete({
        source: search_URL,   // The search results as a JSON file
        minLength: 2,       // Only AJAX search if there are >= 2 chars entered

        // Custom focus function to handle our custom results format
        focus: function(event, ui) {
            search_box.val(ui.item.value);
            return false;
        },

        // When an item is selected, bypass the search results and go directly
        // to the item's detail page. We do this by looking up the item's URL
        // and setting the window location appropriately.
        select: function(event, ui){
            window.location = lookup_URL + "?type=" + ui.item.type +
                    "&hostname=" + ui.item.value;
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
}
