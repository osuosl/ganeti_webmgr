function dropdownToLabel(dropdown, ignoreOpt){
    /*
    Conditionally convert dropdowns to labels. 
    
    I.e. if the specified, dropdown has only one option, select that option, 
    hide the dropdown, and replace it with a label of that option. Note that 
    'dropdown' must be a jQuery object.
        
    If ignoreOpt is supplied, options with called ignoreOpt will be ignored and
    treated as if they don't exist. This is useful if the dropdown has "blank"
    options such as "-----" or "- choose one -" etc.

    Note that it might be nice to make this into a jQuery plugin
    eventually.
    */

    var optElems = dropdown.find('option');
    var opts = [];
    var PROCESSED_OP_ID = "singleOptionDropdownLabel";
    var processedOpElems = dropdown.siblings().filter('.'+PROCESSED_OP_ID);

    // create a new list of options sans any "blanks", if specified
    if(ignoreOpt != undefined){
        optElems.each(function(i, opt){
            if($(opt).text() != ignoreOpt)
                opts.push(opt);
        });

    // otherwise just use the options as is
    } else {
        opts = optElems;
    }

    // if there's only one option, not including "blank" options if 
    // specified, select it, hide the dropdown, and replace it with a label of
    // the same option.
    if(opts.length == 1){
        $(opts).attr('selected', 'selected');
        dropdown.hide();
        dropdown.change();
        
        // if no processed options (label versions of the single-option 
        // dropdown) make the label
        if(processedOpElems.length == 0){
            dropdown.parent().append(
                "<div class='"+PROCESSED_OP_ID+" disabledText'>" + 
                    $(opts).text() + 
                "</div>");
        }

    // otherwise, replace the processed option, if it exists, with a label
    } else {
        dropdown.show();
        processedOpElems.remove();
    }
}
