function helpTips(selector) {
    // Inputs which have a help tip.
    var $form_fields = $('input, select', selector);
    var $tips = $('div[id^="help-"]');
    // Hide help tips with javascript by default.
    // With no js, the tips will still be there.
    $tips.hide()
    /* Binds the event to our inputs,
       passing the focused element to the handler. */
    $form_fields.live('focus', this, getHelpTips);

    function getHelpTips(event) {
        // The name of the input corresponds to the help tip's data-help attribute.
        var help_name = this.name;
        var $tip = $('#help-'+help_name);
        // Fix for old helptip labels
        if ($tip.children('h3').length == 0) {
            var id = $(this).attr('id');
            var label = $("label[for='" + id + "']").html();
            $tip.prepend($("<h3>").html(label));
        }
        // Hide all tips.
        $tips.hide()
        // Show the tip.
        $tip.show();
    }
}

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

        // Handle the special case of NIC link field, where prev is mode, not label.
        var prevprev_label = $(this).prev().prev('label');
        if (prevprev_label.text().substring(3,0)==="NIC"){
            label = prevprev_label.html();
        }

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
