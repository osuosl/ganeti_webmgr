function multi_input(scope) {
    // the scope in which we're working (dont mess with other inputs)
    var $scope = $(scope);
    // hide all empty inputs that are not the first input
    $scope.filter(function() {
            return $(this).data('group') != "0";
        }).filter(function() {
            return !$(this).val();
        }).parents('tr').hide();

    // button elements
    var $add = $('<a class="icon add multi"></a>');
    var $del = $('<a class="icon delete multi"></a>');

    function first_hidden() {
        return $scope.parents('tr:hidden:first');
    }
    function last_visible() {
        return $scope.parents('tr:visible:last');
    }

    function place_buttons(){
        // Cache it so we dont ask for it twice
        var visible = last_visible();
        $add.appendTo( visible.children('td').first() );
        $del.appendTo( visible.children('td').first() );
    }

    // Add click handlers to both buttons
    $add.click(function(e) {
        e.preventDefault();
        // Get the first hidden tr within our scope
        var first = first_hidden();
        // Grab the input inside's group #
        var group_num = $('.multi:not(.icon)', first).data('group');
        // Get all items within our scope with that same group #
        var group = $("[data-group="+group_num+"]").filter($scope);
        // Show each of those inputs
        group.each(function(index) {
            $(this).parents('tr').show();
        });
        // Place buttons next to the last visible item within our scope
        place_buttons();
    });

    $del.click(function(e) {
        e.preventDefault();
        // Cache the last item so we dont recompute it multiple times
        var last = last_visible();
        var group_num = $('.multi:not(.icon)', last).data('group');
        // Do not hide/remove the only/first group.
        if (group_num == 0) { return; }
        var group = $(".multi:not(.icon)[data-group="+group_num+"]").filter($scope);
        group.each(function(index) {
            $(this).val('').parents('tr').hide();
        });
        place_buttons();
    });

    // Initialization!
    place_buttons();
}
