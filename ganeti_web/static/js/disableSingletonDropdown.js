$(function() {
    /*
     * Transform <select> elements with only one single option into labels and
     * hidden fields.
     *
     * Since disabled <select> elements will not be submitted with a form,
     * instead this function transforms such elements into hidden <input>
     * elements and adds a label which contains the text of the choice made
     * through the <select>.
     *
     * Unlike its predecessor, this function operates on *all* <select>
     * elements in the document.
     */

    $("select").each(function(i, select) {
        if (select.options.length == 1) {
            var $option = $(select.options[0]);
            var $select = $(select);
            var val = $option.val();
            // select the option
            $select.val(val)
            // get the id/css/display text and apply it to our new element
            var display = $option.html()
            var id = $select.attr('id');
            var classes = $select.attr('class');
            var $element = $("<span />").attr('id', id)
                                        .attr('class', classes)
                                        .html(display);

            // add our new element right after the select and hide the dropdown
            $select.after($element);
            $select.hide();
        }
    });
});
