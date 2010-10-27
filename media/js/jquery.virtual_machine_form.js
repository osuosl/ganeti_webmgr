(function($){
    /* Virtual machines init function to
        setup selectors and hide/show of snode
        */
    virtual_machines = function() {
        cluster = $("#id_cluster");
        owner = $("#id_owner");
        snode = $("#id_snode");
        disk_template = $("#id_disk_template");
        curSelection = $("#id_snode option:selected").index();
        if( disk_template.val() != 'drdb') {
            snode.parent().hide();
        }
        disk_template.change(function() {
            if( disk_template.val() == 'drdb') {
                snode.parent().show();
            } else {
                snode.parent().hide();
            }
        });
        snode.change(function() {
            if( snode.attr('readonly') ) {
                $("#id_snode option:selected").removeAttr('selected');
                $("#id_snode option").index(curSelection).attr('selected');
            }
        });
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