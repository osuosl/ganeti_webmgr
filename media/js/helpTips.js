function initHelpTips(selector){
    /* initialize the help tips for each item on the create VM template */

    $(selector).find('input, select')
            .live('focus', helpTip);

    function helpTip(){
        console.log($(this));
        var name = this.name;
        var label = $(this).prev('label').html();
        var content = $('#help-'+name);
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