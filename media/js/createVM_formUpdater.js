function formUpdater(url_choices, url_options, url_defaults){
    /* Live form updating for the create VM template */
    
    // -----------
    // class data
    // -----------
    var cluster =               $("#id_cluster");
    var owner =                 $("#id_owner");
    var snode =                 $("#id_snode").parent();
    var pnode =                 $("#id_pnode").parent();
    var niclink =               $("#id_nic_link").parent();
    var disk_template =         $("#id_disk_template");
    var nicmode =               $("#id_nic_mode");
    var curSelection =          $("#id_snode option:selected").index();
    var iallocator =            $("#id_iallocator");
    var iallocator_hostname =   $("#id_iallocator_hostname");
    var bootOrder =             $("#id_boot_order");
    var imagePath =             $("#id_cdrom_image_path");
    var using_str =             ' Using: ';
    var blankOptStr =           '---------';
    var nodes =                 null; // nodes available

    // ------------
    // init stuffs
    // ------------
    this.init = function(){
        /* initialize the live form updator */

        // disable the iallocator stuff by default
        if(!iallocator_hostname.attr('value')){
            iallocator.attr('readonly', 'readonly');
        } else{
            iallocator.after(
                "<span>" + 
                    using_str + iallocator_hostname.val() +
                "</span>"
            );
        }
        _iallocatorDisable();
    
        // hide CD-ROM Image Path stuffs by default
        _imagePathHide();

        // setup form element change hooks
        _initChangeHooks();

        // fire off some initial changes
        iallocator.change();
        disk_template.change();
        bootOrder.change();
        
        // process the owner dropdown, i.e., if it only has a single option, 
        // select it, and make the dropdown read-only
        disableSingletonDropdown(owner, blankOptStr);
    }
    
    function _initChangeHooks(){
        /* setup change hooks for the form elements */

        // boot device change
        bootOrder.change(function(){
            /* 
            Only show image path stuffs if CD-ROM is selected in the boot 
            order dropdown.
            */
            var dropdown = $(this);
            var id = $(this).children("option:selected").val();
            if(id == 'cdrom'){
                _imagePathShow();
            } else {
                _imagePathHide();
            }
        });

        // iallocator change
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
                if(!iallocator.is(':checked')){
                    pnode.show();
                    disk_template.change();
                }
            }
        });

        // disk_template change
        disk_template.change(function() {
            if(!iallocator.is(':checked') || 
                    iallocator.attr('readonly')) {

                if(disk_template.val() == 'drbd' && nodes && nodes.length > 1){
                    snode.show();
                } else {
                    snode.hide();
                }
            }
        });

        // owner change
        owner.change(function() {
            var dropdown = $(this);
            var id = $(this).children("option:selected").val();

            if(id != '') {
                // JSON update the cluster when the owner changes
                $.getJSON(url_choices, {'clusteruser_id':id}, function(data){
                    var oldcluster = cluster.val();

                    cluster.children().not(':first').remove();
                    $.each(data, function(i, item) {
                        cluster.append(_newOpt(item[0], item[1]));
                    });

                    // Try to re-select the previous cluster, if possible.
                    cluster.val(oldcluster);

                    // process dropdown if it's a singleton
                    disableSingletonDropdown(cluster, blankOptStr);

                    // trigger a change in the cluster
                    cluster.change();
                });
            }
        });

        // cluster change
        cluster.change(function() {
            var pnode       = $("#id_pnode");
            var snode       = $("#id_snode");
            var oslist      = $("#id_os");
            var dropdown    = $(this);
            var id = $(this).children("option:selected").val();
            
            if( id != '' ) {
                // JSON update oslist, pnode, and snode when cluster changes
                $.getJSON(url_options, {'cluster_id':id}, function(data){
                    var oldpnode = pnode.val();
                    var oldsnode = snode.val();
                    var oldos = oslist.val();

                    pnode.children().not(':first').remove();
                    snode.children().not(':first').remove();
                    oslist.children().not(':first').remove();
                    $.each(data, function(i, items) {
                        $.each(items, function(key, value) {
                            if( i == 'nodes' ) {
                                child = _newOpt(value, value);
                                child2 = child.clone();
                                pnode.append(child);
                                snode.append(child2);
                            }
                            else if (i == 'os') {
                                child = _newOptGroup(value[0], 
                                        value[1]);
                                oslist.append(child);
                            }
                        });
                    });

                    // make nodes publically available
                    nodes = data['nodes'];

                    // Restore old choices from before, if possible.
                    pnode.val(oldpnode);
                    snode.val(oldsnode);
                    oslist.val(oldos);

                    // And finally, do the singleton dance.
                    disableSingletonDropdown(pnode, blankOptStr);
                    disableSingletonDropdown(snode, blankOptStr);
                    disableSingletonDropdown(oslist, blankOptStr);
                });

                // only load the defaults if errors are not present 
                if($(".errorlist").length == 0){
                    $.getJSON(url_defaults, {'cluster_id':id}, function(d){
                        /* fill default options */

                        // boot device dropdown
                        if(d['boot_order']) {
                            $("#id_boot_order :selected").removeAttr(
                                'selected');
                            $("#id_boot_order [value=" + d['boot_order'] + "]")
                                .attr('selected','selected');
                        }
                        
                        // hypervisors
                        if(d['hypervisors']) {
                            //list - do nothing for now.
                        }

                        // iallocator checkbox
                        if(d['iallocator'] != "" && 
                                d['iallocator'] != undefined){
                            if(!iallocator_hostname.attr('value')) {
                                iallocator_hostname.attr('value',
                                        d['iallocator']);
                                if(iallocator.siblings("span").length == 0){
                                    iallocator.after(
                                        "<span>" + using_str +
                                            d['iallocator'] + 
                                        "</span>"
                                    );
                                }
                            }
                            // Check iallocator checkbox
                            iallocator.show();
                            iallocator.siblings().show();
                            iallocator.removeAttr('disabled');
                            iallocator.removeAttr('readonly');
                            iallocator.attr('checked', 'true');
                            iallocator.change();
                        } else {
                            _iallocatorDisable();
                        }

                        // kernel path text box
                        if(d['kernel_path']){
                            $("#id_kernel_path").val(d['kernel_path']);
                        } else {
                            $("#id_kernel_path").val('');
                        }

                        // nic mode dropdown
                        if(d['nic_mode']) {
                            $("#id_nic_mode :selected").removeAttr('selected');
                            $("#id_nic_mode [value=" + d['nic_mode'] + "]")
                                .attr('selected','selected');
                        } else { 
                            $("#id_nic_mode :first-child")
                                .attr('selected', 'selected');
                        }

                        // nic link text box
                        if(d['nic_link']){
                            $("#id_nic_link").val(d['nic_link']);
                        }
                        
                        // nic type dropdown
                        if(d['nic_type']) {
                            $("#id_nic_type :selected").removeAttr('selected');
                            $("#id_nic_type [value=" + d['nic_type'] + "]")
                                .attr('selected','selected');
                        }

                        // memory text box
                        if(d['memory']){
                            $("#id_memory").val(d['memory']);
                        }

                        // disk type dropdown
                        if(d['disk_type']){
                             $("#id_disk_type").val(d['disk_type']);
                        }
                        
                        // root path text box
                        if(d['root_path']){
                            $("#id_root_path").val(d['root_path']);
                        } else {
                            $("#id_root_path").val('/');
                        }
                        
                        // enable serial console checkbox
                        if(d['serial_console']){
                            $("#id_serial_console").attr('checked', true);
                        }
                        
                        // virtual CPUs text box
                        if(d['vcpus']){
                            $("#id_vcpus").val(d['vcpus']);
                        }
                        
                        // image path text box
                        if(d['cdrom_image_path']){
                            $("#id_cdrom_image_path").val(d['cdrom_image_path']);
                        }
                    });
                }
            }
        });
    }

    // ----------------
    // private helpers
    // ----------------
    function _imagePathHide(){
        imagePath.hide();
        imagePath.siblings().hide();
    }

    function _imagePathShow(){
        imagePath.show();
        imagePath.siblings().show();
    }

    function _iallocatorDisable(){
        /* Disable and hide all of the iallocator stuffs */
        iallocator.hide();
        iallocator_hostname.removeAttr('value')
        iallocator.siblings().hide();
        iallocator.attr('disabled', 'disabled');
        iallocator.removeAttr('checked');
        iallocator.change();
    }

    function _newOpt(value, text) {
        /* Create new option items for select field */
        o = $("<option></option>");
        o.attr("value", value);
        o.attr("text", text);
        return o;
    }

    function _newOptGroup(value, options) {
        /* Create new option group for select field */
        group = $("<optgroup></optgroup>");
        group.attr("label", value);
        $.each(options, function(i, option) {
            group.append(_newOpt(option[0], option[1]));
        });
        return group;
    }
}
