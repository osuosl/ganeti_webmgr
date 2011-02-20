function formUpdater(url_choices, url_options, url_defaults){
    /* Live form updating for the create VM template */
    
    // -----------
    // class data
    // -----------
    var cluster =               $("#id_cluster");
    var owner =                 $("#id_owner");
    var snode =                 $("#id_snode").parent();
    var pnode =                 $("#id_pnode").parent();
    var niclink =               $("#id_niclink").parent();
    var disk_template =         $("#id_disk_template");
    var nicmode =               $("#id_nicmode");
    var curSelection =          $("#id_snode option:selected").index();
    var iallocator =            $("#id_iallocator");
    var iallocator_hostname =   $("#id_iallocator_hostname");
    var bootOrder =             $("#id_bootorder");
    var imagePath =             $("#id_imagepath");
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
                    cluster.children().not(':first').remove();
                    $.each(data, function(i, item) {
                        child = $("<option> </option>");
                        child.attr('value', item[0]);
                        child.attr('text', item[1]);
                        cluster.append(child);
                    });

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

                                disableSingletonDropdown(pnode, blankOptStr);
                                disableSingletonDropdown(snode, blankOptStr);
                            }
                            else if (i == 'os') {
                                child = _newOptGroup(value[0], 
                                        value[1]);
                                oslist.append(child);

                                disableSingletonDropdown(oslist,
                                        blankOptStr);
                            }
                        });
                    });

                    // make nodes publically available
                    nodes = data['nodes'];
                });

                // only load the defaults if errors are not present 
                if($(".errorlist").length == 0){
                    $.getJSON(url_defaults, {'cluster_id':id}, function(d){
                        /* fill default options */

                        // boot device dropdown
                        if(d['bootorder']) {
                            $("#id_bootorder :selected").removeAttr(
                                    'selected');
                            $("#id_bootorder [value=" + d['bootorder'] + "]")
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
                        if(d['kernelpath']){
                            $("#id_kernelpath").val(d['kernelpath']);
                        } else {
                            $("#id_kernelpath").val('');
                        }

                        // nic mode dropdown
                        if(d['nicmode']) {
                            $("#id_nicmode :selected").removeAttr('selected');
                            $("#id_nicmode [value=" + d['nicmode'] + "]")
                                .attr('selected','selected');
                        } else { 
                            $("#id_nicmode :first-child")
                                .attr('selected', 'selected');
                        }

                        // nic link text box
                        if(d['niclink']){
                            $("#id_niclink").val(d['niclink']);
                        }
                        
                        // nic type dropdown
                        if(d['nictype']) {
                            $("#id_nictype :selected").removeAttr('selected');
                            $("#id_nictype [value=" + d['nictype'] + "]")
                                .attr('selected','selected');
                        }

                        // memory text box
                        if(d['ram']){
                            $("#id_ram").val(d['ram']);
                        }

                        // disk type dropdown
                        if(d['disktype']){
                             $("#id_disk_type").val(d['disktype']);
                        }
                        
                        // root path text box
                        if(d['rootpath']){
                            $("#id_rootpath").val(d['rootpath']);
                        } else {
                            $("#id_rootpath").val('/');
                        }
                        
                        // enable serial console checkbox
                        if(d['serialconsole']){
                            $("#id_serialconsole").attr('checked', true);
                        }
                        
                        // virtual CPUs text box
                        if(d['vcpus']){
                            $("#id_vcpus").val(d['vcpus']);
                        }
                        
                        // image path text box
                        if(d['imagepath']){
                            $("#id_imagepath").val(imagepath);
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
