(function( $ ){
    $.fn.select_all = function() {
    /* Multicheckbox selector */

        var form = this;
        //If checkboxes are 0 then do not show at all
        if (this.find('input[type=checkbox]').size() > 0) {

            var selectorbox = $("<input>")
                .attr(
                {
                    type:  'checkbox',
                    checked:	false,
                    id: 'checkboxsel'
                })
                .click(function()
                {
                    var checked_status = this.checked;
                    form.find("input[type=checkbox]").each(function()
                    {
                        this.checked = checked_status;
                    });
                });
            var selectorlabel =  $("<label>")
                .attr({
                    "for":  'checkboxsel'
                })
                .text("Select All: ");

            selectorlabel.insertBefore(form);
            selectorbox.insertBefore(form);
        }
    }

})( jQuery );
