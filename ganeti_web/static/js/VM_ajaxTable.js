function ajaxTable(URL, TABLE_ID){
    /* A server-side-sortable, paginator-enabled table for the 
     * virtual_machine/table.html template.
     */

    // ============
    // Object data
    // ============
    var FETCH_ARGS = {page:1};
    var current_order_by = null;
    var spinner = null;

    // =======
    // Get ID
    // =======
    this.getID = function(){
        /* Get this table's CSS ID, complete with the '#' */
        return '#' + TABLE_ID;
    };

    // ===========
    // Initialize
    // ===========
    this.init = function(){
        /* Initialize this AJAX table */

        var THIS_TABLE = this;
        var TABLE_ID = this.getID();
        
        spinner = $(TABLE_ID + ' .spinner');

        // ----------
        // Paginator
        // ----------
        function paginator_prev(e){
            /* Paginator previous button handler. Decrements page number. */
            e.preventDefault();
            FETCH_ARGS["page"] = FETCH_ARGS["page"] - 1;
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .previous').live('click', paginator_prev);

        function paginator_next(e){
            /* Paginator next button handler. Increments page number. */
            e.preventDefault();
            FETCH_ARGS["page"] = FETCH_ARGS["page"] + 1;
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .next').live('click', paginator_next);

        function paginator_jumpTo(){
            /* Paginator jump-to button handler. Sets page to specific page */
            FETCH_ARGS["page"] = parseInt($(this).html());
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .page:not(.active)')
                .live('click', paginator_jumpTo);

        // --------------
        // Table sorting
        // --------------
        $(TABLE_ID + ' #vmlist th').live("click", function(){
            var $this = $(this);
            var field = $this.html();
            var order_by = $this.attr("order_by");
            if(field == current_order_by && $this.hasClass("ascending")){
                $this.addClass("descending").removeClass("ascending");
                order_by = "-" + order_by;
            } else {
                $(TABLE_ID + ' #vmlist th').removeClass('ascending')
                        .removeClass('descending');
                $this.addClass("ascending");
            }
            FETCH_ARGS["page"] = 1;
            FETCH_ARGS["order_by"] = order_by;
            current_order_by = field;
            THIS_TABLE.update();
        });

        // hide the spinner initially
        spinner.hide();
    };

    // =============
    // Update table
    // =============
    this.update = function(){
        /* Update the table using AJAX depending on current page and sorting 
         * order.
         */
        var TABLE_ID = this.getID();

        // Show load spinner thing, hide the table contents
        spinner.show();
        $(TABLE_ID + ' #vmlist tr td').hide();
        $(TABLE_ID + ' #vm-wrapper .pagination').hide();

        // AJAX load the table contents, push results into table
        $.get(URL, FETCH_ARGS, function(results){
            var $results = $("<div id='results'>"+results+"</div>");
            var tbody = $results.find("tbody");
            var pagination = $results[2];
            $(TABLE_ID + ' #vm-wrapper .pagination').replaceWith(pagination);
            $(TABLE_ID + ' #vmlist tbody').replaceWith(tbody);

            // Hide load spinner thing
            spinner.hide();
        }, "html");
    }
}

