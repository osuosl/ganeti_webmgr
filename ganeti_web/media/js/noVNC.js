/*
 * Copyright (C) 2010 Oregon State University et al.
 * 
 * Javascript for custom noVNC interface.
 */

var PROXY_REQUEST_URI;
var POPOUT_URL;

$(function () {

    var popout = $('#popout');

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

    $('#connect').click(function() {
        var $this = $(this);
        if($this.hasClass('enabled')) {
            rfb.disconnect();
            connected = false;
        } else {
            connected = true;
            start();
        }
        return false;
    });

    $('#encrypt').click(function(){
        var $this = $(this);
        if (!connected) {
            if ($this.hasClass('enabled')){
                $('#encrypt_check').attr('checked',false);
                $this.removeClass('enabled')
            } else {
                $('#encrypt_check').attr('checked',true);
                $this.addClass('enabled')
            }
        }
        return false;
    });

    $('#ctrlaltdelete')
        .click(function(){
            if (!$(this).hasClass('disabled')) {
                rfb.sendCtrlAltDel();
            }
            return false;
        });

    if (POPOUT_URL != undefined) {
        popout.show();
        popout.click(function(event) {
            event.preventDefault();
            var url;
            if (rfb == undefined) {
                url = POPOUT_URL;
            } else {
                url = POPOUT_URL + '?auto_connect=1';
                stop();
            }
            window.open(url, 'popout', 'height=450,width=812,status=no,toolbar=no,menubar=no,location=no');
        });
    }



    // users exits the page by following link or closing the tab or sth else
    $(window).bind("unload", stop);


    function show_errors() {
        if (host===false || port===false || password===false) {
            connected = false;
            $("#VNC_status_bar")
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
            $('#connect')
                .addClass('enabled')
                .html('Disconnect');
            $('#ctrlaltdelete').removeClass('disabled')
        } else {
            connected = false;
            $('#connect')
                .removeClass('enabled')
                .html('Connect');
            $('#ctrlaltdelete').addClass('disabled')
        }

        if (msg != undefined) {
            $('#VNC_status_bar')
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
        $("#vnc_errors").hide();
        $.ajax({
            "async": false,
            "url": PROXY_REQUEST_URI,
            "dataType": "json",
            "success": function(data, s, x){
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
            'encrypt':      $('#encrypt_check').attr('checked') ? true : false,
            'true_color':   true,
            'local_cursor': true,
            'shared':       true,
            'updateState':  updateState
        });
        rfb.connect(host, port, password);
        return false;
    }
});