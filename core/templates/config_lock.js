var lock = false;
var timeout = undefined;
var active = true;
var lock_interval = undefined;

function start_activity_tracking(){
    timeout = setTimeout(timed_out,30000)
    $('body')
        .mousemove(activity)
        .keypress(activity);
}

function activity(){
    /*
        called whenever activity is detected.  This function will prevent
        the time_out function from being called
    */
    if (timeout!=undefined) {
        clearTimeout(timeout);
    }
    timeout = setTimeout(timed_out,180000)
}

function timed_out(){
    /*
        called when the owner of the lock times out
    */
    clearTimeout(lock_interval);
    $('body')
        .unbind('mousemove',activity)
        .unbind('keypress',activity)
        .mousemove(reacquire_lock)
        .keypress(reacquire_lock);
    $errors.empty().append('<li>Your lock has timed out due to inactivity.  If you become active again it will automatically be reacquired if the page is not in use by another user.</li>')
    $errors.show();
    lock = false;
    active = false;
}

function reacquire_lock() {
    /*
        called when a timed out user tries to reacquire the lock
    */
    if (!active){
        active = true
        $('body')
            .unbind('mousemove',reacquire_lock)
            .unbind('keypress',reacquire_lock);
        refresh_lock();
    }
}

function acquire_lock() {
    /*
        called by users wishing to obtain the lock.  The result of this method
        may be cached.
    */
    $.get('{{ROOT}}/plugin/lock/acquire', {}, process_lock);
}

function refresh_lock() {
    /*
        called by owner of lock to maintain possession
    */
    $.get('{{ROOT}}/plugin/lock/refresh', {}, process_lock);
}

function process_lock(data){
    /*
        processes response about lock possession
    */
    if (active){
        if (data == 1){
            if (!lock){
                // only hide on lock acquire, otherwise you could hide an important error
                start_activity_tracking()
                $errors.hide();
                lock = true;
            }
            lock_interval = setTimeout(refresh_lock, 10000);
        } else {
            $errors.empty().append('<li>You do not hold the lock.  You cannot edit configuration until $USER is finished.<br/>  Page will unlock when lock is acquired.</li>')
            $errors.show();
            lock = false;
            setTimeout(acquire_lock, 10000);
        }
    }    
}