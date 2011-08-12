function formUpdater(url_choices, url_options, url_defaults){
    /* Live form updating for the create VM template */
    
    // -----------
    // class data
    // -----------
    var cluster =               $("#id_cluster");
    var owner =                 $("#id_owner");
    var snode =                 $("#id_snode").parent("p");
    var pnode =                 $("#id_pnode").parent("p");
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
    var iallocator =            $("#id_iallocator");
    var iallocator_hostname =   $("#id_iallocator_hostname");
    var boot_order =            $("#id_boot_order");
    var image_path =            $("#id_cdrom_image_path").parent("p");
    var image2_path =           $("#id_cdrom2_image_path").parent("p");
    var root_path =             $("#id_root_path");
    var kernel_path =           $("#id_kernel_path");
    var serial_console =        $("#id_serial_console").parent("p");
    var no_install =            $("#id_no_install");
    var start =                 $("#id_start").parent("p");
    var using_str =             " Using: ";
    var blankOptStr =           "---------";
    var nodes =                 null; // nodes available
    var oldid; // global for hypervisor.change function

    var template_choices = $("\
            <option value=''>---------</option>\
            <option value='plain'>plain</option>\
            <option value='drbd'>drbd</option>\
            <option value='file'>file</option>\
            <option value='diskless'>diskless</option>\
        ".toString());

    var single_node_template_choices = $("\
            <option value=''>---------</option>\
            <option value='plain'>plain</option>\
            <option value='file'>file</option>\
            <option value='diskless'>diskless</option>\
        ".toString());

    // ------------
    // cluster defaults
    // ------------
    var DEFAULT_NIC_MODE = undefined;
    var DEFAULT_NIC_LINK = undefined;

    // ------------
    // init stuffs
    // ------------
    this.init = function(cluster_defaults){
        /* initialize the live form updater */

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
        var def_iallocator = cluster_defaults['iallocator'];
        if (!iallocator.is(":checked")
            && (def_iallocator == undefined|| def_iallocator == '')
        ){
            _iallocatorDisable();
        }
        
        // hide CD-ROM Image Path stuffs by default
        _imagePathHide();
        
        // setup form element change hooks
        _initChangeHooks();

        //recover from form error
        if(no_install.is(":checked")){
            start.hide();
        }

        // fire off some initial changes
        iallocator.change();
        disk_template.change();
        boot_order.change();
        hypervisor.change();

        disableSingletonDropdown($("#id_pnode"), blankOptStr);
        // process the owner dropdown, i.e., if it only has a single option, 
        // select it, and make the dropdown read-only
        disableSingletonDropdown(owner, blankOptStr);
        disableSingletonDropdown(hypervisor, blankOptStr);
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

        // boot device change
        boot_order.live("change", function(){
            /* 
            Only show image path stuffs if CD-ROM is selected in the boot 
            order dropdown.
            */
            var id = $(this).children("option:selected").val();
            if(id == "cdrom"){
                _imagePathShow();
            } else {
                _imagePathHide();
            }
        });

        // iallocator change
        iallocator.live("change", function() {
            if(!iallocator.attr("readonly")) {
                if(iallocator.is(":checked")) {
                    pnode.hide();
                    snode.hide();
                } else {
                    pnode.show();
                    disk_template.change();
                }
            } else {
                if(!iallocator.is(":checked")){
                    pnode.show();
                    disk_template.change();
                }
            }
        });

        // disk_template change
        disk_template.live("change", function() {
            if(!iallocator.is(":checked") || 
                    iallocator.attr("readonly")) {

                if(disk_template.val() == "drbd" && nodes && nodes.length > 1){
                    snode.show();
                } else {
                    snode.hide();
                }
            }

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

        // owner change
        owner.live("change", function() {
            var id = $(this).children("option:selected").val();
            if(id != "") {
                // JSON update the cluster when the owner changes
                _cached_get(url_choices, {"clusteruser_id":id}, _update_cluster_choices);
            }
        });

        //no-install change
        no_install.live("change",function() {
            if(no_install.is(":checked")){
                start.hide();
            } 
            else{
                start.show();
            }
        });

        // cluster change
        cluster.live("change", function() {
            var id = $(this).children("option:selected").val();
            if( id != "" ) {
                // JSON update oslist, pnode, and snode when cluster changes
                _cached_get(url_options, {"cluster_id":id}, _update_options);

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

    function _update_cluster_choices(data){
        var oldcluster = cluster.val();

        cluster.children().not(":first").remove();
        $.each(data, function(i, item) {
            cluster.append(_newOpt(item[0], item[1]));
        });

        // Try to re-select the previous cluster, if possible.
        cluster.val(oldcluster);

        // process dropdown if its a singleton
        disableSingletonDropdown(cluster, blankOptStr);

        // trigger a change in the cluster
        cluster.change();
    }

    function _update_options(data) {
        var snode       = $("#id_snode");
        var oslist      = $("#id_os");
        var child, child2;
        var oldpnode = pnode.val();
        var oldsnode = snode.val();
        var oldos = oslist.val();
        var old_template = disk_template.val();

        pnode.children().not(":first").remove();
        snode.children().not(":first").remove();
        oslist.children().not(":first").remove();
        $.each(data, function(i, items) {
            $.each(items, function(key, value) {
                if( i == "nodes" ) {
                    child = _newOpt(value, value);
                    child2 = child.clone();
                    pnode.append(child);
                    snode.append(child2);
                }
                else if (i == "os") {
                    child = _newOptGroup(value[0],
                            value[1]);
                    oslist.append(child);
                }
            });
        });

        // make nodes publically available
        nodes = data["nodes"];

        // update disk template choices
        disk_template.empty();
        if (nodes.length == 1){
            disk_template.html(single_node_template_choices);
        } else {
            disk_template.html(template_choices);
        }

        // Restore old choices from before, if possible.
        pnode.val(oldpnode);
        snode.val(oldsnode);
        oslist.val(oldos);
        disk_template.val(old_template);

        // And finally, do the singleton dance.
        disableSingletonDropdown(pnode, blankOptStr);
        disableSingletonDropdown(snode, blankOptStr);
        disableSingletonDropdown(oslist, blankOptStr);
    }

    function _update_cluster_defaults(d, status, xhr){
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
            boot_order.find("[value=" + d["boot_order"][0] + "]")
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

        // iallocator checkbox
        if(d["iallocator"] != "" &&
                d["iallocator"] != undefined){
            if(!iallocator_hostname.attr("value")) {
                iallocator_hostname.attr("value",
                        d["iallocator"]);
                if(iallocator.siblings("span").length == 0){
                    iallocator.after(
                        "<span>" + using_str +
                            d["iallocator"] +
                        "</span>"
                    );
                }
            }
            // Check iallocator checkbox
                iallocator.parent("p").show();
                iallocator.removeAttr("disabled")
                    .removeAttr("readonly")
                    .attr("checked", "checked")
                    .change();
            } else {
                _iallocatorDisable();
            }

            // kernel path text box
            if(d["kernel_path"]){
                kernel_path.val(d["kernel_path"]);
            } else {
                kernel_path.val("");
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
            //second cdrom
            if(d["cdrom2_image_path"]){
                image2_path.find("input").val(d["cdrom2_image_path"]);
            }
            disableSingletonDropdown(hypervisor, blankOptStr);
        }

    function _fillDefaultOptions(cluster_id, hypervisor_id) {
        var args = new Object();
        args["cluster_id"] = cluster_id;
        if(typeof hypervisor_id != undefined) {
            args["hypervisor"] = hypervisor_id;
        }
        _cached_get(url_defaults, args, _update_cluster_defaults);
    }



    function _imagePathHide(){
        image_path.hide();
        image2_path.hide();
    }

    function _imagePathShow(){
        image_path.show();
        image2_path.show();
    }

    function _iallocatorDisable(){
        /* Disable and hide all of the iallocator stuffs */
        iallocator.parent("p").hide();
        iallocator_hostname.removeAttr("value")
            .parent("p").hide();
        iallocator.attr("disabled", "disabled")
            .removeAttr("checked")
            .change();
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

    var AJAX_CACHE = {};
    function _cached_get(url, data, callback) {
        var key = _encode_url(url, data);
        var response = AJAX_CACHE[key];
        if (response == undefined ) {

            // create a callback function that will execute for all calls to
            // this url.  helps deal with multiple simultaneous calls to a url
            var _callback = function(response, status, xhr) {
                AJAX_CACHE[key] = response;
                var callbacks = _callback.callbacks;
                for (var i in callbacks) {
                    callbacks[i](response, status, xhr);
                }
            };

            // add callback to generic callback function
            _callback.callbacks = [];
            if (callback != undefined) {
                _callback.callbacks.push(callback);
            }
            
            $.getJSON(url, data, _callback);
            AJAX_CACHE[key] = _callback;
        } else if (callback != undefined) {
            if (response.callbacks != undefined) {
                _push_unique(response.callbacks, callback);
            } else {
                callback(response);
            }
        }
    }

    function _push_unique(array, item) {
       for (var i in array) {
           if (array[i] == item) {
               return;
           }
       }
       array.push(item);
    }

    function _encode_url(url, data)
    {
       var ret = [];
       for (var d in data)
          ret.push(encodeURIComponent(d) + "=" + encodeURIComponent(data[d]));
       return url+'?'+ret.join("&");
    }

}

