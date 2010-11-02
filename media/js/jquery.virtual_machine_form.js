(function($){
    /* Virtual machines init function to
        setup selectors and hide/show of snode
        */
    virtual_machines = function() {
        cluster = $("#id_cluster");
        owner = $("#id_owner");
        snode_parent = $("#id_snode").parent();
        pnode_parent = $("#id_pnode").parent();
        disk_template = $("#id_disk_template");
        curSelection = $("#id_snode option:selected").index();
        iallocator = $("#id_iallocator");
        iallocator.attr('checked', true);
        iallocator.change(function() {
            if(iallocator.is(':checked')) {
                pnode_parent.hide();
                snode_parent.hide();
            } else {
                pnode_parent.show();
                disk_template.change();
            }
        });
        iallocator.change();
        disk_template.live('change', function() {
            if(!iallocator.is(':checked')){
                if( disk_template.val() == 'drdb') {
                    snode_parent.show();
                } else {
                    snode_parent.hide();
                }
            }
        });
        disk_template.change();
    };
    /* Create new option items for select field */
    newoption = function(value) {
        o = $("<option></option>");
        o.attr("value", value);
        o.attr("text", value);
        return o;
    };
    /* Ajax request to update cluster when owner changes */
    owner_change = function(url) {
        owner.change(function() {
            id = $(this).children("option:selected").val();
            if( id != '' ) {
                $.getJSON(url,
                    {'group_id':id}, function(data) {
                        cluster.children().not(':first').remove();
                        $.each(data, function(i, item) {
                                child = $("<option> </option>");
                                child.attr('value', item[0]);
                                child.attr('text', item[1]);
                                cluster.append(child);
                        });
                });
            }
            cluster.trigger('change');
        });
    };
    /* Ajax request to update oslist, pnode, and snode when cluster changes */
    cluster_change = function(url) {
        cluster.change(function() {
            pnode = $("#id_pnode");
            snode = $("#id_snode");
            oslist = $("#id_os");
            id = $(this).children("option:selected").val();
            if( id != '' ) {
                $.getJSON(url, {'cluster_id':id},
                    function(data) {
                        pnode.children().not(':first').remove();
                        snode.children().not(':first').remove();
                        oslist.children().not(':first').remove();
                        $.each(data, function(i, items) {
                            $.each(items, function(key, value) {
                                child = newoption(value);
                                if( i == 'nodes' ) {
                                    child2 = child.clone();
                                    pnode.append(child);
                                    snode.append(child2);
                                }
                                else if ( i == 'os' ) {
                                    oslist.append(child);
                                }
                            });
                        });
                    });
            }
        });
    };
})(jQuery);