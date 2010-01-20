var lock = false;

function acquire_lock() {
    $.get('{{ROOT}}/plugin/lock', {}, process_lock);
}

function process_lock(data){
    /*
        processes response about lock acquisition
    */
    if (data == -2){
        //timeout, refresh but give enough time for someone else to
        //obtain the lock
        $errors.empty().append('<li>Your lock has timed out.  It will refresh automatically in 30 seconds, during this time other users may acquire the lock.  If you interact with the page the lock will be reacquired.</li>')
        $errors.show();
        setTimeout(acquire_lock, 30000);
        lock = false;
        return;
    }else if (data == 1){
        $errors.hide();
        lock = true;
    } else {
        $errors.empty().append('<li>You do not hold the lock.  You cannot edit configuration until $USER is finished.<br/>  Page will unlock when lock is acquired.</li>')
        $errors.show();
        lock = false;
    }
    setTimeout(acquire_lock, 10000);
}