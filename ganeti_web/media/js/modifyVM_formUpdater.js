function modifyFormUpdater(nic_count_original) {
    /* Functions for the modify form */

    // Security Model and Domain
    var security_domain = $("#id_security_domain").parent();
    var security_model = $("#id_security_model");

    // VNC TLS, x509 Path, and x509 Verify
    var vnc_tls = $("#id_vnc_tls");
    var vnc_x509_path = $("#id_vnc_x509_path");
    var vnc_x509_path_field = vnc_x509_path.parent();
    var vnc_x509_verify = $("#id_vnc_x509_verify");

    // Tmp variables for path and verify
    var tmp_vnc_x509_path = "";
    var tmp_vnc_x509_verify = false;

    // NICs
    var nic_count = $("#id_nic_count");
    var nics = $("#nics");
    var nic_add =    $("#nics .add");
    var nic_delete = $("#nics .delete");

    this.init = function() {
        // Hide vnc_x509_path and verify if checkbox enabled
        if( !vnc_tls.is(':checked')) {
            vnc_x509_path_field.hide();
            vnc_x509_verify.parent().hide();
        }

        _initChangeHooks();
    };

    /**
     * If security model is anything other than user
     *  security domain is hidden.
     */
    security_model.change(function() {
        if ($(this).children("option:selected").val() == 'user') {
            security_domain.show();
        } else {
            security_domain.hide();
        }
    }).trigger('change');

    /**
     * Deselecting VNC TLS will save the state of
     *  vnc_x509_verify, and value of vnc_x509_path,
     *  before clearing both fields.
     * Selecting VNC TLS will set these values back
     *  to their original state and value before VNC
     *  TLS was deselected.
     */
     vnc_tls.change(function() {
        if ($(this).is(':checked')) {
            // Set vnc_x509_path to origin path
            vnc_x509_path.attr('value', tmp_vnc_x509_path);
            // Change state of checkbox
            if (tmp_vnc_x509_verify) {
                vnc_x509_verify.attr('checked', true);
            }
            // Show vnc_x509_path and vnc_x509_verify
            vnc_x509_path_field.show();
            vnc_x509_verify.parent().show();
            // Show Error Messages
            prev = vnc_x509_path_field.prev();
            if (prev[0].tagName == 'UL') {
               prev.show();
            }
        } else {
            // Save path and checkbox state
            tmp_vnc_x509_path = vnc_x509_path.val();
            tmp_vnc_x509_verify = vnc_x509_verify.is(':checked');
            // Set path to '' and disable checkbox state
            vnc_x509_path.attr('value', '');
            vnc_x509_verify.removeAttr('checked');
            // Hide vnc_x509_path and vnc_x509_verify
            vnc_x509_path_field.hide();
            vnc_x509_verify.parent().hide();
            // Hide Error messages
            prev = vnc_x509_path_field.prev();
            if (prev[0].tagName == 'UL') {
               prev.hide();
            }
        }
    });

    function _initChangeHooks(){
        /* setup change hooks for the form elements */

        nic_add.click(_add_nic);
        nic_delete.live("click",_remove_nic);

        //XXX reset nic count, sometimes the browser remembers old values.
        nic_count.val(nics.children('p').length);
        //XXX hide delete buttons for everything but the last element
        nics.children('.delete').not(':last').hide();
    }

    function _add_nic() {
        var count = nic_count.val();
        if (count < nic_count_original+1) {
            nic_count.val(parseInt(count)+1);
            var p = $('<p></p>');
            var label = $("<label>NIC/" + count +"</label>");
            var mac = $('<input type="text"/>');
            mac.attr("name", "nic_mac_" + count);
            mac.attr("id", "id_nic_mac_" + count);
            var link = $("#nics input[name^=nic_link]").first().clone();
            link.attr("name", "nic_link_" + count);
            link.attr("id", "id_nic_link_" + count);
            p.append(label);
            p.append(mac);
            p.append(link);
            nics.append(p);
            nics.append('<div class="icon delete"></div>');
            
            if (count == nic_count_original){
                nic_add.addClass('disabled');
            }
        }
    }

    function _remove_nic() {
        /**
         * Delete a nic.  If this is a nic currently on the virtualmachine it is
         * just disabled.  Even if a new nic is added
         */
        var count = nic_count.val();
        nic_count.val(parseInt(count)-1);
        var button = $(this);
        button.prev("p").remove();
        button.prev("ul").remove();
        button.remove();

        if (count < nic_count_original+2){
            nic_add.removeClass('disabled');
        }

        // renumber remaining disks
        var i = 0;
        $('#nics p').each(function(){
            $(this).children('label').html("NIC/" + i);
            $(this).children('input[name^=nic_link]').each(function(){
                $(this)
                    .attr("name", "nic_link_" + i)
                    .attr("id", "id_nic_link_" + i);
            });
            $(this).children('input[name^=nic_mac]').each(function(){
                $(this)
                    .attr("name", "nic_mac_" + i)
                    .attr("id", "id_nic_mac_" + i);
            });
            i++;
        });
    }
}

