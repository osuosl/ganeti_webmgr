/**
 * Django CSRF protection for Ajax requests.  This script adds a CSRF token to
 * all POST requests sent using jquery ajax functions.  This ensures that all
 * POST requests will be proected even when they do not submit a form.
 *
 * This script expects that DOMAIN is set to the domain & port of the host
 *   e.g. "localhost:8000"
 */

$(document).ready(function() {
    $('html').ajaxSend(function(event, xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        // Only send the token locally.  Check for both relative urls, and
        // absolute urls to the domain.
        var url = settings.url;
        var absolute_https = new RegExp("^https:\/\/"+window.location.host+"\/.*");
        var absolute_http = new RegExp("^http:\/\/"+window.location.host+"\/.*");
        if (
            !(/^http:.*/.test(url)|| /^https:.*/.test(url))
            || (absolute_https.test(url) || absolute_http.test(url))
        ) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    });
});