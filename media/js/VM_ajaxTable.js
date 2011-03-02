function ajaxTable(url, tableID){
    /* A server-side-sortable, paginator-enabled table for the 
     * virtual_machine/table.html template.
     */

    var FETCH_ARGS = {page:1};
    var current_order_by = null;

    // get this table's ID
    this.getID = function(){
        return '#' + tableID;
    }

    // paginator stuffs
    this.pageUp = function(){
        console.log("Incrementing page...");
        FETCH_ARGS["page"] = FETCH_ARGS["page"] + 1;
    }

    this.pageDown = function(){
        console.log("Decrementing page...");
        FETCH_ARGS["page"] = FETCH_ARGS["page"] - 1;
    }
    this.setPage = function(page){
        console.log("Updating page number to "+page);
        FETCH_ARGS["page"] = page;
    }

    // -----
    // init 
    // -----
    this.init = function(){
        
        console.log("Initializing table '"+this.getID()+"'...");

        var THIS_TABLE = this;
        var TABLE_ID = this.getID();

        // -----------
        // Pagination 
        // -----------
        // paginator previous
        function paginator_prev(e){
            console.log("Previous paginator button clicked.");
            e.preventDefault();
            THIS_TABLE.pageDown();
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .previous').live('click', 
                paginator_prev);


        // paginator next
        function paginator_next(e){
            console.log("Next paginator button clicked.");
            e.preventDefault();
            THIS_TABLE.pageUp();
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .next').live('click', paginator_next);

        // paginator jump-to
        function paginator_jumpTo(){
            console.log("Jump-to paginator button clicked.");
            THIS_TABLE.setPage(parseInt($(this).html()));
            THIS_TABLE.update();
        }
        $(TABLE_ID + ' .pagination .page:not(.active)').live('click', 
                paginator_jumpTo);

        // --------------
        // table sorting
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
        // AJAX load spinny thing
        // -----------------------
        var spinner = $(TABLE_ID + ' .spinner');
        function loadModeOn(){
            console.log("Load mode on. Showing spinner; hiding table.");
            spinner.show();
            $(TABLE_ID + ' #vmlist tr td').hide();
            $(TABLE_ID + ' #vm-wrapper .pagination').hide();
        }
        function loadModeOff(){
            console.log("Load mode off. Hiding spinner.");
            spinner.hide();
        }
        spinner.hide()
            .ajaxStart(loadModeOn)
            .ajaxStop(loadModeOff);
    }

    // ------------
    // ajax update
    // ------------
    this.update = function(){
        /* 
        Update the table using AJAX depending on current page and sorting
        order.
        */
        console.log("Updating table '"+this.getID()+"'...");

        // grab this table's ID to update
        var tableID = this.getID();

        // get call success function must be defined here instead of inside
        // a $.get() lamda function so it can access tableID
        function callSuccess(results){
            console.log("Actuall updating table '"+tableID+"'...");
            $results = $(results);
            tbody = $results.children("tbody");
            pagination = $results[2];
            $(tableID + ' #vm-wrapper .pagination')
                    .replaceWith(pagination);
            $(tableID + ' #vmlist tbody').replaceWith(tbody);
        }
        
        // make the actual get request, call callSuccess on return success
        $.get(url, FETCH_ARGS, callSuccess, "html");
    }
}
