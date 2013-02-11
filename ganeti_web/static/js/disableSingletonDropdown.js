function disableSingletonDropdown(dropdown, ignoreOpt){
    /*
     * "Disable" the specified dropdown if it has only one option.
     *
     * If a dropdown has only a one option, hide it, and replace it with a
     * disabled replica. This is necessary because one cannot simply disable a
     * dropdown because then it will not be sent with a submit.
     *
     * If ``ignoreOpt`` is supplied, options labeled with ``ignoreOpt`` will be
     * ignored and treaded as if they don't exist. This is useful if the
     * dropdown has "blank" options such as "---------" or "- choose one -",
     * etc.
     *
     * Please note that ``dropdown`` must be a jQuery object.
     */
    var optElems = dropdown.find('option');
    var opts = [];
    var PROCESSED_OP_ID = 'singleOptionDropdown';
    var processedOpElems = dropdown.siblings().filter('.'+PROCESSED_OP_ID);
    var old_value = dropdown.val();

    // create a new list of options sans any "blanks", if specified
    if(ignoreOpt != undefined){
        optElems.each(function(i, opt){
            if($(opt).text() != ignoreOpt)
                opts.push(opt);
            });

    // otherwise, just use the options as is
    } else {
        opts = optElems;
    }

    // if there's only one option, not including "blank" options (if specified)
    // select it, hide the dropdown, and replace it with a disabled dropdown of
    // the same option.
    if(opts.length == 1){
        $(opts).attr('selected', 'selected');
        dropdown.hide();
        if (dropdown.val()!=old_value) {
            dropdown.change();
        }

        // if there're no processed options (disabled dropdown versions) make
        // the disabled dropdown
        if(processedOpElems.length == 0){
            dropdown.parent().append(
                "<select class='"+PROCESSED_OP_ID+"' disabled='disabled'>"+
                    "<option selected='selected'>"+
                        $(opts).text()+
                    "</option>"+
                "</select>"
            );
        }

    // otherwise show the original dropdown
    } else {
        dropdown.show();
        processedOpElems.remove();
    }
}

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
            span.addClass('dropdown');
            $(select).after(hidden, span);
            $(select).remove();
        }
    });
}
