function highlight(elemId){
        var elem = $(elemId);
        elem.css("background-color", "#ffffbb");
        setTimeout(function() { $(elemId).animate({ backgroundColor: "white" }, 2000)}, 1500);
    }

       
    $(document).ready( function(){
        if (document.location.hash) {
            highlight(document.location.hash);
        }
        $('a[href*=#]').click(function(){
            var elemId = '#' + $(this).attr('href').split('#')[1];
            highlight(elemId);
        });

    })