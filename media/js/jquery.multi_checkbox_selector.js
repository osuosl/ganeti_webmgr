(function($){
    /* Multicheckbox selector
        */
    check_box_selector = function() {
    	var selectorbox = $("<input>")
    		.attr(
    		{
    			type:  'checkbox',
    			checked:	false,
    			id: 'checkboxsel',
    		})
    		.click(function()				
			{
				var checked_status = this.checked;
				$("input[name=virtual_machines]").each(function()
				{
					this.checked = checked_status;
				});
			});
    	var selectorlabel =  $("<label>")
        	.attr({
        		"for":  'checkboxsel'
        	})
        	.text("Select All: ");
//    	If checkboxes are 0 then do not show at all
    	if ($("input[name=virtual_machines]").size() > 0){
    		selectorlabel.insertBefore('form');
    		selectorbox.insertBefore('form');
    	}
    };
})(jQuery);
