/* JavaScript responsible for making the autocomplete search box work. */

function autocomplete_search(search_box, search_form, JSON_url){
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
     *      `JSON_url`:     The url responsible for returning the search
     *              suggestions as a JSON object, e.g. '/search.json'
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
    
    // Autocomplete search box
    search_box.autocomplete({
        source: JSON_url,
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
}
