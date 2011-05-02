/**
 * Django L18N localization selection.
 */

function setlang(lang){
    $("#langsel").val(lang);
    $("#langform").submit();
}

$(function(){


    $('#language').click(function(event) {
        var $language = $(this);
        var $languages = $('#languages')
        if (!$language.hasClass('open')) {
            $language.addClass('open');
            $languages.show();
            $('html').click(function(){
                $language.removeClass('open');
                $languages.hide();
                $(this).unbind('click');
            });
            event.stopPropagation();
        }
    });
});