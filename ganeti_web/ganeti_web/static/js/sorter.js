function sort(url, old_order, new_order) { 
    var order = getOrderAscDesc(old_order, new_order);
    location.href = url.replace(old_order, order);
} 

function getOrderAscDesc(old_order, new_order) {
    if (old_order == new_order) {
        return '-' + old_order;
    }
    else {
        return new_order;
    }
}
