(function($){
    /* 
    Virtual machines init function to
    setup selectors and hide/show of snode
    */
    virtual_machines = function() {
        cluster = $("#id_cluster");
        owner = $("#id_owner");
        var snode = $("#id_snode").parent();
        var pnode = $("#id_pnode").parent();
        var niclink = $("#id_niclink").parent();
        disk_template = $("#id_disk_template");
        nicmode = $("#id_nicmode");
        curSelection = $("#id_snode option:selected").index();
        iallocator = $("#id_iallocator");
        iallocator_hostname = $("#id_iallocator_hostname");
        using_str = ' Using: '
        if( !iallocator_hostname.attr('value') ) {
            iallocator.attr('readonly', 'readonly');
        } else {
            iallocator.after("<span>"+using_str+iallocator_hostname.val()+
                    "</span>");
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
            } else {
                if(!iallocator.is(':checked')) {
                    pnode.show();
                    disk_template.change();
                }
            }
        });
        iallocator.change();
        disk_template.change(function() {
            if(!iallocator.is(':checked') || iallocator.attr('readonly')) {
                if( disk_template.val() == 'drbd') {
                    snode.show();
                } else {
                    snode.hide();
                }
            }
        });
        disk_template.change();
       
    };
    /* Create new option items for select field */
    newoption = function(value, text) {
        o = $("<option></option>");
        o.attr("value", value);
        o.attr("text", text);
        return o;
    };
    /* Create new option group for select field */
    newoptgroup = function(value, options) {
        group = $("<optgroup></optgroup>");
        group.attr("label", value);
        $.each(options, function(i, option) {
            group.append(newoption(option[0], option[1]));
        });
        return group;
    };
    /* Ajax request to update cluster when owner changes */
    owner_change = function(url) {
        owner.change(function() {
            id = $(this).children("option:selected").val();
            if( id != '' ) {
                $.getJSON(url,
                    {'clusteruser_id':id}, function(data) {
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
                                if( i == 'nodes' ) {
                                    child = newoption(value, value);
                                    child2 = child.clone();
                                    pnode.append(child);
                                    snode.append(child2);
                                }
                                else if ( i == 'os' ) {
                                    child = newoptgroup(value[0], value[1]);
                                    oslist.append(child);
                                }
                            });
                        });
                    });
                $.getJSON(url2, {'cluster_id':id},
                        function(data) {
                            bootorder = data['bootorder'];
                            iallocator_default = data['iallocator'];
                            hypervisors = data['hypervisors'];
                            vcpus = data['vcpus'];
                            rootpath = data['rootpath'];
                            ram = data['ram'];
                            disktype = data['disktype'];
                            kernelpath = data['kernelpath'];
                            nicmode = data['nicmode'];
                            niclink = data['niclink'];
                            nictype = data['nictype'];
                            imagepath = data['imagepath'];
                            if(bootorder) {
                                $("#id_bootorder :selected").removeAttr(
                                        'selected');
                                $("#id_bootorder [value="+bootorder+"]").attr(
                                        'selected','selected');
                            }
                            if(hypervisors) {
                                //list - do nothing for now.
                            }
                            if(iallocator_default) {
                                if( !iallocator_hostname.attr('value')) {
                                    iallocator_hostname.attr('value',
                                            iallocator_default);
                                    if(iallocator.siblings("span").length 
                                            == 0){
                                        iallocator.after("<span>"+using_str+
                                                iallocator_default+"</span>");
                                    }
                                }
                                // Check iallocator checkbox
                                iallocator.removeAttr('readonly');
                                iallocator.attr('checked', 'checked');
                                iallocator.change();
                            } else {
                                iallocator.siblings("span").remove();
                                iallocator_hostname.removeAttr('value')
                                iallocator.attr('readonly', 'readonly');
                                iallocator.attr('checked', false);
                                iallocator.change();
                            }
                            if(kernelpath) {
                                $("#id_kernelpath").val(kernelpath);
                            } else {
                                $("#id_kernelpath").val('');
                            }
                            if(nicmode) {
                                $("#id_nicmode :selected").removeAttr(
                                        'selected');
                                $("#id_nicmode [value="+nicmode+"]").attr(
                                        'selected','selected');
                            } else {
                                $("#id_nicmode :first-child").attr('selected', 
                                        'selected');
                            }
                            if(niclink){
                                $("#id_niclink").val(niclink);
                            }
                            if(nictype) {
                                $("#id_nictype :selected").removeAttr(
                                        'selected');
                                $("#id_nictype [value="+nictype+"]").attr(
                                        'selected','selected');
                            }
                            if(ram) {
                                $("#id_ram").val(ram);
                            }
                            if(disktype){
                                 $("#id_disk_type").val(disktype);
                            }
                            if(rootpath) {
                                $("#id_rootpath").val(rootpath);
                            } else {
                                $("#id_rootpath").val('/');
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
