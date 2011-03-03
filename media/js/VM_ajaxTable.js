function ajaxTable(url, tableID){
    /* A server-side-sortable, paginator-enabled table for the 
     * virtual_machine/table.html template.
     */

    // ============
    // Object data
    // ============
    var FETCH_ARGS = {page:1};
    var current_order_by = null;

    // =======
    // Get ID
    // =======
    this.getID = function(){
        /* Get this table's CSS ID, complete with the '#' */
        return '#' + tableID;
    }

    // ===========
    // Initialize
    // ===========
    this.init = function(){
        /* Initialize this AJAX table */

        var THIS_TABLE = this;
        var TABLE_ID = this.getID();

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
            var page = parseInt($(this).html());
            FETCH_ARGS["page"] = page;
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .page:not(.active)')
                .live('click', paginator_jumpTo);

        // --------------
        // Table sorting
        // --------------
        $(TABLE_ID + ' #vmlist th').live("click", function(){
            $this = $(this)
            field = $this.html();
            order_by = $this.attr("order_by");
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

        // -----------------------
        // AJAX loading indicator
        // -----------------------
        var spinner = $(TABLE_ID + ' .spinner');
        function loadModeOn(){
            /* AJAX load indicator handler. Show spinny thing, hide table. */`
            spinner.show();
            $(TABLE_ID + ' #vmlist tr td').hide();
            $(TABLE_ID + ' #vm-wrapper .pagination').hide();
        }
        function loadModeOff(){
            /* AJAX load indicator off. Hide spinny thing. */
            spinner.hide();
        }
        spinner.hide()
            .ajaxStart(loadModeOn)
            .ajaxStop(loadModeOff);
    }

    // =============
    // Update table
    // =============
    this.update = function(){
        /* Update the table using AJAX depending on current page and sorting 
         * order.
         */
        var TABLE_ID = this.getID();

        function callSuccess(results){
            /* AJAX load call success handler. Push results into table. */
            $results = $(results);
            tbody = $results.children("tbody");
            pagination = $results[2];
            $(TABLE_ID + ' #vm-wrapper .pagination').replaceWith(pagination);
            $(TABLE_ID + ' #vmlist tbody').replaceWith(tbody);
        }
        $.get(url, FETCH_ARGS, callSuccess, "html");
    }
}

