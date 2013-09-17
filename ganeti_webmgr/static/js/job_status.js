/** @namespace data.opresult */

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
function format_op(op, stat) {
    op = op.substring(3).toLowerCase();
    op = op.replace(/_/g, " ");
    str = cap_first(op) + ": " + cap_first(stat);
    return str;
}

function JobPoller() {
    var actions_enabled;
    var get_interval;
    var get_interval_speed;
    var get_jobs_url = '';
    var messages = $('#messages');
    var callback;
    var errback;
    var cluster;
    this.FAST = 3000;
    this.SLOW = 60000;
    var get_xhr = undefined;
    var poller;


    this.init = function (url, new_cluster, new_callback, new_errback) {
        poller = this;
        get_jobs_url = url;
        cluster = new_cluster;
        callback = new_callback==undefined ? $.noop : new_callback;
        errback = new_errback==undefined ? $.noop : new_errback;
    };

    // poll for active jobs.  This maintains the list of jobs that are being
    // actively queried for updates.  This will pull in new jobs started elsewhere
    this.poll = function (interval) {
        interval = interval==undefined ? poller.SLOW : interval;
        if (get_interval_speed != interval) {
            if (get_interval != undefined) {
                clearInterval(get_interval);
            }
            get_interval_speed = interval;
            get_interval = setInterval(poller.get_jobs, interval);
        }
    };


    // get list of active jobs
    this.get_jobs = function () {
        /* Run the AJAX call. if a call is pending, just skip this one */
        if (get_xhr == undefined) {
            get_xhr = $.ajax({
                url: get_jobs_url,
                error: errback,
                success: function(data) {
                    get_xhr = undefined;
                    process_get_jobs(data);
                }
            });
        }
    };


    // process list of active jobs.  This will import new jobs if any are not being
    // tracked already
    function process_get_jobs(data) {
        var active = [];
        for (var i in data) {
            var job_data = data[i];
            if (job_data.status == 'success') {
                callback();
            } else {
                poller.render_job(job_data);
                active.push(job_data.id);
                if (job_data.status == 'error') {
                    errback();
                }
            }
        }

        // clear any jobs that weren't in the active list any more
        $('#messages').children('.job').each(function(){
            var job_id = this.id.substring(4);
            if (active.indexOf(job_id) == -1) {
                if (!$(this).hasClass('error')) {
                    callback();
                }
                $(this).remove();
            }
        });

        if (data.length==0) {
            poller.poll(poller.SLOW);
        } else {
            poller.poll(poller.FAST);
        }
    }


    function active_op(data) {
        /* Find a sub-operation which has not successfully completed. */
        for (var sub_op = 0; sub_op < data['opstatus'].length; sub_op++) {
            if (data['opstatus'][sub_op] != 'success') {
                return sub_op;
            }
        }
        return sub_op;
    }


    this.render_job = function (data) {
        var job_id = data['id'];
        var html = $('#job_'+job_id);
        var op_index = active_op(data);
        var status = data['status'];
        var op = format_op(data['ops'][op_index]['OP_ID'], status);
        var new_job = (html.length==0);

        if (new_job) {
            html = $("<li class='job'><h3>"+op+"</h3></li>");
            html.attr('id', 'job_'+job_id);
            html.addClass(status);
            $('#messages').append(html);
            html.append('<div class="scrollable"><div class="detector"></div></div>');
        }

        var error = undefined;
        var scrollable = html.children('.scrollable');

        if (status=='running' || status=='error') {
            html.addClass(status);

            if (data.status == 'error' && html.find('pre.error').length==0) {
                var reason = data.opresult[op_index][1][0];
                var href = cluster + "/job/" + job_id + "/clear/";
                html.children('h3')
                .append("<a class='clear' title='clear error' href='"+href+"'></a>");
                error = $("<pre class='error'>" + reason + "</pre>");
                scrollable.prepend(error);
                actions_enabled = true;
                $('#actions a').removeClass('disabled');
            }

            // append log messages that are not already displayed
            var current_log_count = html.find(".op_log ul li").length;
            if (data['oplog'][op_index].length != 0) {
                var log_html = html.find('.op_log');
                if (log_html.length==0){
                    log_html = $("<pre class='op_log'><ul></ul></pre>");
                    scrollable.append(log_html);
                }
                var log = data['oplog'][op_index];
                for (var i=current_log_count; i<log.length; i++) {
                    log_html.children("ul")
                    .append("<li>"+log[i][3]+"</li>");
                }
            }

            // XXX hack to ensure log area is same width as error area.
            var width = undefined;
            if (log_html != undefined) {
                width = $(html).find('.scrollable .detector').width();
                width -= (log_html.innerWidth() - log_html.width()); // subtract padding
                log_html.width(width);
                $(html).find('.scrollable').css('display', 'block')
            } else if (error != undefined) {
                width = error.width();
                $(html).find('.scrollable .detector').width(width);
                $(html).find('.scrollable').css('display', 'block')
            }
        }
    };

    $("#messages a.clear").live("click", function(event){
        event.preventDefault();
        var error = $(this).parent().parent();
        $.post(this.href, function(){
            error.remove();
        });
    });
}
