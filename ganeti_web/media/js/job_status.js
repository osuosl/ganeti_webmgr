/** @namespace data.opresult */

var checkInterval;
var actions_enabled;

// poll for job status, first poll is delayed by 3000ms
function poll_job_status(cluster, job_id, callback, errback) {
    actions_enabled = false;
    $('#actions a').addClass('disabled');
    checkInterval = setInterval(get_job_status, 3000, cluster, job_id, callback, errback);
}

// Get job status.
// The cluster should be the URL corresponding to a cluster slug.
function get_job_status(cluster, job_id, callback, errback) {
    /* On success, clear the interval and run the callback. */
    on_success = function() {
        clearInterval(checkInterval);
        if (callback != undefined) {
            callback();
        }
    }

    /* On error, clear the interval and run the errback. */
    on_error = function() {
        clearInterval(checkInterval);
        if (errback != undefined) {
            errback();
        }
    }

    /* Run the AJAX call. */
    $.ajax({
        url: cluster + "/job/" + job_id + "/status/",
        error: on_error,
        success: function(data) {
            if (data.status == 'success') {
                $("#messages").empty();
                on_success();
            } else if (data.status == 'error') {
                on_error();
            }

            display_job(cluster, data);
        }
    });
}

function display_job(cluster, data) {
    /* Find a sub-operation which has not successfully completed. There
     * probably will be only one. */
    for (var sub_op = 0; sub_op < data['opstatus'].length; sub_op++) {
        if (data['opstatus'][sub_op] != 'success') {
            break;
        }
    }

    $("#messages").empty();

    var op = format_op(data['ops'][sub_op]['OP_ID']);
    var html = $("<li class='job'><h3>"+op+"</h3></li>");
    $("#messages").append(html);
    var scrollable = $('<div class="scrollable"><div class="detector"></div></div>');
    var error = undefined;
    html.append(scrollable);

    if (data.status == 'error') {
        html.addClass('error');
        var reason = data.opresult[sub_op][1][0];
        var job_id = data['id'];
        var href = cluster + "/job/" + job_id + "/clear/";
        html.children('h3')
        .append("<a class='clear' title='clear error' href='"+href+"'></a>");
        error = $("<pre class='error'>" + reason + "</pre>");
        scrollable.append(error);
        actions_enabled = true;
        $('#actions a').removeClass('disabled');
    }

    // append log messages that are not already displayed
    var current_log_count = $("#log ul li").length;
    if (data['oplog'][sub_op].length != 0) {
        var log_html = html.children('.op_log');
        if (log_html.length==0){
            log_html = $("<pre class='op_log'><ul></ul></pre>");
            scrollable.append(log_html);
        }
        var log = data['oplog'][sub_op];
        for (var i=current_log_count; i<log.length; i++) {
            log_html.children("ul")
            .append("<li>"+log[i][3]+"</li>");
        }
    }

    // XXX hack to ensure log area is same width as error area.
    if (log_html != undefined) {
        var width = $(html).find('.scrollable .detector').width()
        width -= (log_html.innerWidth() - log_html.width()) // subtract padding
        log_html.width(width);
        $(html).find('.scrollable').css('display', 'block')
    }
}

/* Capitalize the first letter of every word in a string. */
function cap_first(str) {
    var a = str.split(" ");
    var len = a.length;

    for (var i = 0; i < len; i++) {
        a[i] = a[i][0].toUpperCase() + a[i].substring(1);
    }

    return a.join(" ");
}

/* Format an operation string.
 *
 * Operation strings look like "OP_DO_SOMETHING". They should be formatted to
 * appear as "Do Something". */
function format_op(str) {
    str = str.substring(3).toLowerCase();
    str = str.replace(/_/g, " ");
    str = cap_first(str);
    return str;
}

$("#messages a.clear").live("click", function(event){
    event.preventDefault();
    var error = $(this).parent().parent();
    $.post(this.href, function(){
        error.fadeOut(1000, function(){
            error.remove();
        });
    });
});
