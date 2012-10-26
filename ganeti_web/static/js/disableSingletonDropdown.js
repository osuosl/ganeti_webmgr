function disableSingletonDropdown2() {
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
            var option = select.options[0];
            var hidden = $("<input type='hidden' />");
            hidden.attr({
                name: select.name,
                value: option.value,
            });
            var span = $("<span />");
            span.html(option.innerHTML);
            $(select).after(hidden, span);
            $(select).remove();
        }
    });
}
