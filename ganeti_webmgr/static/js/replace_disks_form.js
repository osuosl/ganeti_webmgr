$(function() {
    /* Live form updating for the create VM template */
    
    // -----------
    // class data
    // -----------
    var mode =                  $("#id_mode");
    var node =                  $("#id_node");
    var iallocator =            $("#id_iallocator");
    var iallocator_hostname =   $("#id_iallocator_hostname");
    var using_str =             " Using: ";

    // ------------
    // init stuffs
    // ------------
    function init(){
        /* initialize the live form updater */
        _initChangeHooks();

        // disable the iallocator stuff by default
        if(!iallocator_hostname.attr("value")){
            iallocator.attr("readonly", "readonly");
        } else{
            iallocator.after(
                "<span>" + 
                    using_str + iallocator_hostname.val() +
                "</span>"
            );
        }

        // only disable iallocator by default if there is no cluster selected
        // or the cluster already selected does not support iallocator
        var def_iallocator = iallocator_hostname.val();
        if (!iallocator.is(":checked")
            && (def_iallocator == undefined|| def_iallocator == '')
        ){
            _iallocatorDisable();
        }
        
        // fire off some initial changes
        iallocator.change();
        mode.change();
    }
    
    function _initChangeHooks(){
        /* setup change hooks for the form elements */
        // iallocator change
        iallocator.live("change", function() {
            if(!iallocator.attr("readonly")) {
                if(iallocator.is(":checked")) {
                    _nodeDisable();
                } else {
                    _nodeEnable();
                }
            } else {
                if(!iallocator.is(":checked")){
                    _nodeEnable();
                }
            }
        });

        mode.live("change", function(){
            if ('replace_new_secondary' == mode.val()) {

                var def_iallocator = iallocator_hostname.val();
                if (def_iallocator == undefined || def_iallocator == ''){
                    _nodeEnable();
                } else {
                    _iallocatorEnable();
                }

            } else {
                _iallocatorDisable();
                _nodeDisable();
            }
        })
    }

    function _nodeEnable(){
        /* Disable and hide all of the node stuffs */
        node.parent().parent().show();
        node.removeAttr("disabled")
            .change();
    }

    function _iallocatorEnable(){
        /* Disable and hide all of the iallocator stuffs */
        iallocator.parent().parent("tr").show();
        iallocator.removeAttr("disabled")
            .change();
    }

    function _nodeDisable(){
        /* Disable and hide all of the node stuffs */
        node.parent().parent().hide();
        node.attr("disabled", "disabled")
            .change();
    }

    function _iallocatorDisable(){
        /* Disable and hide all of the iallocator stuffs */
        iallocator.parent().parent("tr").hide();
        iallocator.attr("disabled", "disabled")
            .change();
    }

    init();
});

