function formUpdater(url_options, url_defaults){
    /* Live form updating for the create VM template */
    
    // -----------
    // class data
    // -----------
    var cluster =               $("#id_cluster");
    var hypervisor =            $("#id_hypervisor");
    var disk_type =             $("#id_disk_type");
    var disks =                 $("#disks");
    var disk_count =            $("#id_disk_count");
    var disk_add =              $("#disks .add");
    var disk_delete =           $("#disks .delete");
    var nics =                  $("#nics");
    var nic_count =             $("#id_nic_count");
    var nic_add =               $("#nics .add");
    var nic_delete =            $("#nics .delete");
    var nic_type =              $("#id_nic_type");
    var nic_link =              $("#nics input[name^=nic_link]");
    var disk_template =         $("#id_disk_template");
    var nic_mode =              $("#nics select[name^=nic_mode]");
    var boot_order =            $("#id_boot_order");
    var image_path =            $("#id_cdrom_image_path").parent("p");
    var root_path =             $("#id_root_path");
    var kernel_path =           $("#id_kernel_path");
    var serial_console =        $("#id_serial_console").parent("p");
    var blankOptStr =           "---------";
    var oldid; // global for hypervisor.change function

    // ------------
    // cluster defaults
    // ------------
    var DEFAULT_NIC_MODE = undefined;
    var DEFAULT_NIC_LINK = undefined;

    // ------------
    // init stuffs
    // ------------
    this.init = function(){
        /* initialize the live form updater */

        // setup form element change hooks
        _initChangeHooks();

        // fire off some initial changes
        disk_template.change();
        boot_order.change();
        hypervisor.change(); 
        cluster.change();

        disableSingletonDropdown(cluster, blankOptStr);
    };
    
    function _initChangeHooks(){
        /* setup change hooks for the form elements */

        // handle hypervisor changes
        hypervisor.live("change", function() {
            var id = $(this).val();
            if (id == "xen-hvm") {
                _showHvmKvmElements();
                _hidePvmKvmElements();
                _hideKvmElements();
            } 
            else if (id == "xen-pvm") {
                _showPvmKvmElements();
                _hideHvmKvmElements();
                _hideKvmElements(); 
            }
            else if (id == "kvm") {
                _showKvmElements();
                _showHvmKvmElements();
                _showPvmKvmElements();
            } else {
                return;
            } 
            if(id != oldid && oldid != undefined) {
                _fillDefaultOptions(cluster.val(), id);
            }
            oldid = id;
        });

        // disk_template change
        disk_template.live("change", function() {
            if (disk_template.val() == 'diskless') {
                disks.hide();
                disk_count.val(0);
                disks.find('input[name^=disk_size]').attr('disabled','disabled');
            } else if (!disks.is(":visible") || true) {
                disks.show();
                disks.find('input[name^=disk_size]').removeAttr('disabled');
                disk_count.val(disks.find('input[name^=disk_size]').length);
            }
        });

        // cluster change
        cluster.live("change", function() {
            var child;
            var oslist      = $("#id_os");
            var id = $(this).children("option:selected").val();
            
            if( id != "" ) {
                // JSON update oslist, pnode, and snode when cluster changes
                $.getJSON(url_options, {"cluster_id":id}, function(data){
                    var oldos = oslist.val();

                    oslist.children().not(":first").remove();
                    $.each(data, function(i, items) {
                        $.each(items, function(key, value) {
                            if (i == "os") {
                                child = _newOptGroup(value[0],
                                        value[1]);
                                oslist.append(child);
                            }
                        });
                    });

                    // Restore old choices from before, if possible.
                    oslist.val(oldos);

                    // And finally, do the singleton dance.
                    disableSingletonDropdown(oslist, blankOptStr);
                });

                // only load the defaults if errors are not present 
                if($(".errorlist").length == 0){
                    _fillDefaultOptions(id);   
                }
            }
        });

        disk_add.click(_add_disk);
        disk_delete.live("click",_remove_disk);
        nic_add.click(_add_nic);
        nic_delete.live("click",_remove_nic);
    }

    // ----------------
    // private helpers
    // ----------------
    function _fillDefaultOptions(cluster_id, hypervisor_id) {
        var args = new Object();
        args["cluster_id"] = cluster_id;
        if(typeof hypervisor_id != undefined) {
            args["hypervisor"] = hypervisor_id;
        }
        $.getJSON(url_defaults, args, function(d){
            /* fill default options */

            // boot device dropdown
            if(d["boot_devices"]) {
                boot_order.children().remove();
                $.each(d["boot_devices"], function(i, item){
                    boot_order.append(_newOpt(item[0], item[1]));
                }); 
            }
            if(d["boot_order"]) {
                boot_order.find(":selected").removeAttr(
                    "selected");
                boot_order.find("[value=" + d["boot_order"] + "]")
                    .attr("selected","selected");
                boot_order.change();
            }
            
            // hypervisors dropdown
            if(typeof hypervisor_id != undefined) {
                if(d["hypervisors"]) {
                    hypervisor.children().remove();
                    $.each(d["hypervisors"], function(i, item){
                        hypervisor.append(_newOpt(item[0], item[1]));
                    });
                    if(d["hypervisor"]) {
                        if (d["hypervisor"] != "" &&
                            d["hypervisor"] != undefined) {
                            hypervisor.find(":selected").removeAttr(
                                    "selected");
                            hypervisor.find("[value=" + d["hypervisor"] + "]")
                                .attr("selected", "selected");     
                            hypervisor.change();
                        }
                    }
                }
            }

            // kernel path text box
            if(d["kernel_path"]){
                kernel_path.val(d["kernel_path"]);
            }

            // nic mode dropdown
            if(d["nic_mode"]) {
                nic_mode.find(":selected").removeAttr("selected");
                nic_mode.find("[value=" + d["nic_mode"] + "]")
                    .attr("selected","selected");
                DEFAULT_NIC_MODE = d["nic_mode"];
            } else { 
                nic_mode.find(":first-child")
                    .attr("selected", "selected");
            }

            // nic link text box
            if(d["nic_link"]){
                nic_link.val(d["nic_link"]);
                DEFAULT_NIC_LINK = d["nic_link"];
            }
            
            // nic type dropdown
            if(d["nic_types"]) {
                nic_type.children().remove();
                $.each(d["nic_types"], function(i, item){
                    nic_type.append(_newOpt(item[0], item[1]));
                }); 
            }
            if(d["nic_type"]) {
                nic_type.find(":selected").removeAttr("selected");
                nic_type.find("[value=" + d["nic_type"] + "]")
                    .attr("selected","selected");
            }

            // memory text box
            if(d["memory"]){
                $("#id_memory").val(d["memory"]);
            }

            // disk type dropdown
            if(d["disk_types"]){
                disk_type.children().remove();
                $.each(d["disk_types"], function(i, item){
                    disk_type.append(_newOpt(item[0], item[1]));
                });
                if(d["disk_type"]){
                    disk_type.val(d["disk_type"]);
                }
            }
            
            // root path text box
            if(d["root_path"]){
                root_path.val(d["root_path"]);
            } else {
                root_path.val("/");
            }
            
            // enable serial console checkbox
            if(d["serial_console"]){
                $("#id_serial_console")
                    .attr("checked", "checked");
            } else {
                $("#id_serial_console").removeAttr("checked");
            }
            
            // virtual CPUs text box
            if(d["vcpus"]){
                $("#id_vcpus").val(d["vcpus"]);
            }
            
            // image path text box
            if(d["cdrom_image_path"]){
                image_path.find("input").val(d["cdrom_image_path"]);
            }
            disableSingletonDropdown(hypervisor, blankOptStr);
        });
    }

    function _newOpt(value, text) {
        /* Create new option items for select field */
        var o = $("<option></option>");
        o.attr("value", value);
        o.attr("text", text);
        return o;
    }

    function _newOptGroup(value, options) {
        /* Create new option group for select field */
        var group = $("<optgroup></optgroup>");
        group.attr("label", value);
        $.each(options, function(i, option) {
            group.append(_newOpt(option[0], option[1]));
        });
        return group;
    }
    
    function _hideHvmKvmElements() {
        // Hide hvm + kvm specific hypervisor fields
        boot_order.parent("p").hide();
        image_path.hide(); 
        nic_type.parent("p").hide();
        disk_type.parent("p").hide();
    }

    function _showHvmKvmElements() {
        // Show hvm + kvm specific hypervisor fields
        boot_order.parent("p").show();
        boot_order.change(); 
        nic_type.parent("p").show();
        disk_type.parent("p").show();
    }

    function _hidePvmKvmElements() {
        // Hide pvm specific hypervisor fields
        root_path.parent("p").hide();
        kernel_path.parent("p").hide();
    }

    function _showPvmKvmElements() {
        // Show pvm specific hypervisor fields
        root_path.parent("p").show();
        kernel_path.parent("p").show();
    }

    function _hideKvmElements() {
        // Hide kvm specific hypervisor fields
        serial_console.hide();
    }

    function _showKvmElements() {
        // Show kvm specific hypervisor fields
        serial_console.show();
    }

    function _add_disk() {
        var count = disk_count.val();
        disk_count.val(parseInt(count)+1);
        var p = $('<p></p>');
        var label = $("<label>Disk/" + count+ " Size</label>");
        label.attr('for', "id_disk_size_" + count);
        var input = $('<input type="text"/>');
        input.attr("name", "disk_size_" + count);
        input.attr("id", "id_disk_size_" + count);
        p.append(label);
        p.append(input);
        disks.append(p);
        disks.append('<div class="icon delete"></div>');
    }

    function _remove_disk() {
        var count = disk_count.val();
        disk_count.val(parseInt(count)-1);
        var button = $(this);
        button.prev("p").remove();
        button.prev("ul").remove();
        button.remove();

        // renumber remaining disks
        var i = 0;
        $('#disks p').each(function(){
            $(this).children('label')
                    .html("Disk/" + i + " Size")
                    .attr("for", "id_disk_size_" + i);
            $(this).children('#disks input[name^=disk_size]').each(function(){
                $(this)
                    .attr("name", "disk_size_" + i)
                    .attr("id", "id_disk_size_" + i);
            });
            i++;
        });
    }

    function _add_nic() {
        var count = nic_count.val();
        nic_count.val(parseInt(count)+1);
        var p = $('<p></p>');
        var label = $("<label>NIC/" + count +"</label>");
        
        // create mode select box
        var mode = $('<select></select>');
        mode.append('<option>----------</option>');
        mode.append('<option value="bridged">bridged</option>');
        mode.append('<option value="routed">routed</option>');
        mode.attr("name", "nic_mode_" + count);
        mode.attr("id", "id_nic_mode_" + count);
        if (DEFAULT_NIC_LINK != undefined) {
            mode.val(DEFAULT_NIC_MODE);
        }

        // create link input
        var link = $("<input type='text'/>");
        link.val(DEFAULT_NIC_LINK);
        link.attr("name", "nic_link_" + count);
        link.attr("id", "id_nic_link_" + count);
        if (DEFAULT_NIC_LINK != undefined) {
            mode.val(DEFAULT_NIC_MODE);
        }
        p.append(label);
        p.append(mode);
        p.append(link);
        nics.append(p);
        nics.append('<div class="icon delete"></div>');
    }

    function _remove_nic() {
        var count = nic_count.val();
        nic_count.val(parseInt(count)-1);
        var button = $(this);
        button.prev("p").remove();
        button.prev("ul").remove();
        button.remove();

        // renumber remaining disks
        var i = 0;
        $('#nics p').each(function(){
            $(this).children('label')
                .html("NIC/" + i);
            $(this).children('input[name^=nic_link]').each(function(){
                $(this)
                    .attr("name", "nic_link_" + i)
                    .attr("id", "id_nic_link_" + i);
            });
            $(this).children('select[name^=nic_mode]').each(function(){
                $(this)
                    .attr("name", "nic_mode_" + i)
                    .attr("id", "id_nic_mode_" + i);
            });
            i++;
        });
    }
}

