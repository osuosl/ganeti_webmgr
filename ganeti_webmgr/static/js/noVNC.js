/*
 * Copyright (C) 2010 Oregon State University et al.
 * 
 * Javascript for custom noVNC interface.
 */

var PROXY_REQUEST_URI;
var POPOUT_URL;

$(function () {

    var popout =            $('#popout');
    var connect =           $('#connect');
    var encrypt =           $('#encrypt');
    var encrypt_check =     $('#encrypt_check');
    var ctrlaltdelete =     $('#ctrlaltdelete');
    var vnc_errors =        $("#vnc_errors");
    var vnc_status_bar =    $("#VNC_status_bar");
    var vnc_canvas =        $('#VNC_canvas');
    var vnc_screen =        $('#VNC_screen');

    // XXX remap document.write to a dom function so that it works after DOM is
    // loaded function will be reset after noVNC scripts are loaded.
    var old = document.write;
    document.write = function(str) {$(document).append(str)};
    document.write('<script type="text/javascript" src="'+INCLUDE_URI+'vnc.js"><//script>');
    document.write = old;

    // XXX manually call __initialize().  This normally happens onload, but
    // won't work for us since document may have been loaded already
    if (!Websock_native) {WebSocket.__initialize();}

    var rfb;
    var host, port, password; // VNC proxy connection settings
    var connected = false;

    // When the VNC Canvas is resized, this is called and resizes
    // the window if it's a popup
    function resize_popup() {
        // Height will be VNC_canvas + a little bit
         var cHeight = vnc_canvas.height();
         // Width will be VNC_canvas + a little bit
         var cWidth = vnc_canvas.width();

         // Without this next line, the status hangs off to the right
         // of the buttons. That looks really bad.
         vnc_status_bar.width(cWidth);

         // Resize
         vnc_screen.width(cWidth);
         window.resizeTo(cWidth + 50, cHeight + 100);
    }

    connect.click(function(event) {
        event.preventDefault();
        var $this = $(this);
        if($this.hasClass('enabled')) {
            rfb.disconnect();
            connected = false;
        } else {
            connected = true;
            start();
        }

        // When connecting, change the window size to have
        // the canvas fully viewable
       resize_popup();
    });

    encrypt.click(function(event){
        event.preventDefault();
        var $this = $(this);
        if (!connected) {
            if ($this.hasClass('enabled')){
                encrypt_check.attr('checked',false);
                $this.removeClass('enabled')
            } else {
                encrypt_check.attr('checked',true);
                $this.addClass('enabled')
            }
        }
    });

    ctrlaltdelete
        .click(function(event){
            event.preventDefault();
            if (!$(this).hasClass('disabled')) {
                rfb.sendCtrlAltDel();
            }
        });

    if (POPOUT_URL != undefined) {
        popout.click(function(event) {
            event.preventDefault();
            var url;
            if (rfb == undefined) {
                url = POPOUT_URL;
            } else {
                url = POPOUT_URL + '?auto_connect=1';
                stop();
            }
            window.open(url, 'popout', 'height=550,width=775,status=no,toolbar=no,menubar=no,location=no');
        });
    }

    // users exits the page by following link or closing the tab or sth else
    $(window).bind("unload", stop);


    function show_errors() {
        if (host===false || port===false || password===false) {
            connected = false;
            vnc_status_bar
                .attr("class", "VNC_status_error")
                .html("Probably your proxy is not running or some errors occured. Try again.");
            return false;
        }
        return true;
    }

    function updateState(rfb, state, oldstate, msg) {
        var klass;
        switch (state) {
            case 'failed':
            case 'fatal':
                klass = "VNC_status_error";
                break;
            case 'normal':
                klass = "VNC_status_normal";
                break;
            case 'disconnected':
            case 'loaded':
                klass = "VNC_status_normal";
                break;
            case 'password':
                msg = 'Password required';
                klass = "VNC_status_warn";
                break;
            default:
                klass = "VNC_status_warn";
        }

        if (state == "normal") {
            connected = true;
            connect
                .addClass('enabled')
                .text('Disconnect');
            ctrlaltdelete.removeClass('disabled');
            vnc_canvas.addClass("connected");
        } else {
            vnc_canvas.removeClass("connected");
            connected = false;
            connect
                .removeClass('enabled')
                .text('Connect');
            ctrlaltdelete.addClass('disabled')
        }

        if (msg != undefined) {
            vnc_status_bar
                .attr("class", klass)
                .html(msg);
        }
   }

    function stop() {
         if (rfb != undefined) {
            rfb.disconnect();
            rfb = undefined;
        }
    }

    function start() {
        vnc_errors.hide();

        if (encrypt_check.attr('checked')) {
            is_encrypted = true;
            data = {"tls": true};
        } else {
            is_encrypted = false;
            data = {};
        }

        $.ajax({
            "async": false,
            "url": PROXY_REQUEST_URI,
            "type": "POST",
            "data": data,
            "dataType": "json",
            "success": function(data){
                host = data[0];
                port = data[1];
                password = data[2];
            }
        });
        if (!show_errors()) return false;

        rfb = new RFB({
                            // jQuery doesn't work with that, need to stick
                            // to pure DOM
            'target':       document.getElementById('VNC_canvas'),
            'encrypt':      is_encrypted,
            'true_color':   true,
            'local_cursor': true,
            'shared':       true,
            'updateState':  updateState
        });
        rfb.connect(host, port, password);
        return false;
    }
});
