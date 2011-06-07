function modifyFormUpdater() {
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

    var os = $("#id_os");

    this.init = function() {
        // Hide vnc_x509_path and verify if checkbox enabled
        if( !vnc_tls.is(':checked')) {
            vnc_x509_path_field.hide();
            vnc_x509_verify.parent().hide();
        }
    }

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
}

