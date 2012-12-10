function toggle_boxes(source) {
    checkboxes = document.getElementsByName('chkbx');
    for(var i in checkboxes) {
        checkboxes[i].checked = source.checked;
    }
}

