/*
 * This function takes a selector, and replaces the content of the element with
 * using ajax.
 */
function init_ajax_pagination(event, ui) {
    var panelID = ui.panel.id
    var selector = $("#"+panelID);
    selector.delegate("#paginator a", "click", function(event) {
        event.preventDefault();
        // Ajax url on the link being clicked
        var url = $(this).attr("href");
        // Replace 'selectors' contents with the ajax response.
        selector.load(url);
    });
}
