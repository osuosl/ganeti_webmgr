/*
 * This function is useful for pages which use the jquery-ui tabs functionality.
 *
 * Use is simple. Specify a selector of an <a> element which has an href
 * attribute, and this function will ensure that its contents are loaded inside
 * the current panel using ajax.
 */
function init_ajax_tab_handler(event, ui, selector) {
    var panel = $("#" + ui.panel.id);
    panel.delegate(selector, "click", function(e) {
        e.preventDefault();
        // Ajax url on the link being clicked
        var url = $(this).attr("href");
        // Replace 'selectors' contents with the ajax response.
        panel.load(url);
    });
}
