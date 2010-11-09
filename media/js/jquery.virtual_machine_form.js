(function($){
    /* Virtual machines init function to
        setup selectors and hide/show of snode
        */
    virtual_machines = function() {
        cluster = $("#id_cluster");
        owner = $("#id_owner");
        var snode = $("#id_snode").parent();
        var pnode = $("#id_pnode").parent();
        disk_template = $("#id_disk_template");
        curSelection = $("#id_snode option:selected").index();
        var iallocator = $("#id_iallocator");        
        if( $("#id_iallocator_hostname").length == 0 ) {
            iallocator.attr('readonly', 'readonly');
            iallocator.parent().hide();
        }
        iallocator.change(function() {
            if(!iallocator.attr('readonly')) {
                if(iallocator.is(':checked')) {
                    pnode.hide();
                    snode.hide();
                } else {
                    pnode.show();
                    disk_template.change();
                }
            }
        });
        iallocator.change();
        disk_template.change(function() {
            if(!iallocator.is(':checked') || iallocator.attr('readonly')) {
                if( disk_template.val() == 'drdb') {
                    snode.show();
                } else {
                    snode.hide();
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
    cluster_change = function(url1, url2) {
        cluster.change(function() {
            pnode = $("#id_pnode");
            snode = $("#id_snode");
            oslist = $("#id_os");
            id = $(this).children("option:selected").val();
            if( id != '' ) {
                $.getJSON(url1, {'cluster_id':id},
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
                $.getJSON(url2, {'cluster_id':id},
                        function(data) {
                            iallocator_field = $("#id_iallocator");
                            bootorder = data['bootorder'];
                            iallocator = data['iallocator'];
                            hypervisors = data['hypervisors'];
                            vcpus = data['vcpus'];
                            rootpath = data['rootpath'];
                            ram = data['ram'];
                            kernelpath = data['kernelpath'];
                            nicmode = data['nicmode'];
                            nictype = data['nictype'];
                            imagepath = data['imagepath'];
                            if(bootorder) {
                                $("#id_bootorder :selected").removeAttr('selected');
                                $("#id_bootorder [value="+bootorder+"]").attr('selected','selected');
                            }
                            if(hypervisors) {
                                //list - do nothing for now.
                            }
                            if(iallocator) {
                                // Create input
                                hidden = $("<input type='hidden' />");
                                hidden.attr('id', 'id_iallocator_hostname');
                                hidden.attr('value', iallocator);
                                // Create div and add input
                                hiddendiv = $("<div style='display: none;'>");
                                hiddendiv.append(hidden);
                                hiddendiv.append("</div>");
                                // Append div w/input to page
                                iallocator_field.after(hiddendiv);
                                // Check iallocator checkbox
                                iallocator_field.removeAttr('readonly');
                                iallocator_field.attr('checked', 'checked');
                                iallocator_field.parent().show();
                                iallocator_field.change();
                            } else {
                                iallocator_field.attr('readonly', 'readonly');
                                iallocator_field.parent().hide();
                            }
                            if(kernelpath) {
                                $("#id_kernelpath").val(kernelpath);
                            }
                            if(nicmode) {
                                $("#id_nicmode :selected").removeAttr('selected');
                                $("#id_nicmode [value="+nicmode+"]").attr('selected','selected');
                            }
                            if(nictype) {
                                $("#id_nictype :selected").removeAttr('selected');
                                $("#id_nictype [value="+nictype+"]").attr('selected','selected');
                            }
                            if(ram) {
                                $("#id_ram").val(ram);
                            }
                            if(rootpath) {
                                $("#id_rootpath").val(rootpath);
                            }
                            if(data['serialconsole']) {
                                $("#id_serialconsole").attr('checked', true);
                            }
                            if(vcpus) {
                                $("#id_vcpus").val(vcpus);
                            }
                            if(imagepath) {
                                $("#id_imagepath").val(imagepath);
                            }
                        });
            }
        });
    };
})(jQuery);