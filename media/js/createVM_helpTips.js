function initHelpTips(){
    /* initialize the help tips for each item on the create VM template */
    
    $('#virtualmachineform input, #virtualmachineform select')
            .live('focus', function(){
            
            name = this.name;
            label = $(this).prev('label').html()
            $content = $('#help-'+name);
            
            if($content.length != 0){
                $('#help')
                    .show();
                $('#help div')
                    .empty()
                    .html($content.html());
                $('#help h3')
                    .empty()
                    .html(label);
            }
        });
}
