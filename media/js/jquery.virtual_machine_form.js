(function($){
    init_virtual_machine_form = function() {
        cluster = $("#id_cluster");
        owner = $("#id_owner");
        function newoption(value) {
            o = $("<option></option>");
            o.attr("value", value);
            o.attr("text", value);
            return o;
        }
        cluster.live('change',function() {
            pnode = $("#id_pnode");
            snode = $("#id_snode");
            oslist = $("#id_os");
            id = $(this).children("option:selected").val();
            $.getJSON('{% url instance-create-cluster-options %}', {'cluster_id':id},
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
        });
        owner.live('change',function() {
                id = $(this).children("option:selected").val();
                $.getJSON('{% url instance-create-cluster-choices %}',
                    {'group_id':id}, function(data) {
                        cluster.children().not(':first').remove();
                        $.each(data, function(i, item) {
                                child = $("<option> </option>");
                                child.attr('value', item[0]);
                                child.attr('text', item[1]);
                                cluster.append(child);
                        });
                });
                //cluster.trigger('change');
        });
        snode = $("#id_snode");
        disk_template = $("#id_disk_template");
        curSelection = $("#id_snode option:selected").index();
        if( disk_template.val() != 'drdb') {
            snode.parent().hide();
        }
        disk_template.live('change',function() {
            if( disk_template.val() == 'drdb') {
                snode.parent().show();
            } else {
                snode.parent().hide();
            }
        });
        snode.live('change',function() {
            if( snode.attr('readonly') ) {
                $("#id_snode option:selected").removeAttr('selected');
                $("#id_snode option").index(curSelection).attr('selected');
            }
        });
    };
}) (jQuery);