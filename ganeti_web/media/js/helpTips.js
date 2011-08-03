function initHelpTips(selector){
    /* initialize the help tips for each item on the create VM template */

    $(selector).find('input, select')
            .live('focus', helpTip)
            .end()
            .find('input[type="checkbox"]')
            .live('click', helpTip);
    
    function helpTip(){
        var name = this.name;
        var label = $(this).prev('label').html();

        /* Strip all digits and underscores from end of name.
           Makes things work with unknown number of disks/nics. */
        var content = $('#help-'+name.replace(/[0-9_]*$/,''));

        if(content.length != 0){
            $('#help')
                .show();
            $('#help div')
                .empty()
                .html(content.html());
            $('#help h3')
                .empty()
                .html(label);
        }
    }
}
