
//*****************************************************************************//
//** Functions for converting between slider, MB, and string representations **//
//*****************************************************************************//

function _string_to_slide(str, zeroVal){
    var slide;
    var strVal = parseInt(str);
    if(str.match(/[0-9 ][Gg]/)) { //Gigabytes
        slide = strVal + 9;
    }
    else if(str.match(/[0-9 ][Tt]/)) { //Terabytes
        slide = strVal*1024 + 9;
    }
    else if(parseInt(str)) { //Megabytes
        slide = Math.log(strVal)/Math.log(2);
    }
    else { 
        // zero or non-number entered, set slide to value corresponding to 0MB
        slide = zeroVal;
    }

    return Math.floor(slide);
}

function _string_to_MB(str){
    var MB;
    var strVal = parseFloat(str);
    if(str.match(/[0-9 ][Gg]/)) { //Gigabytes
        MB = strVal*1024;
    }
    else if(str.match(/[0-9 ][Tt]/)) { //Terabytes
        MB = strVal*1024*1024;
    }
    else if(parseInt(str)) { //Megabytes
        MB = strVal;
    }
    else { 
        // zero or non-number entered, set slide to value corresponding to 0MB
        MB = 0;
    }
    return MB;
}

function _MB_to_string(MB){
    var str = '';
    
    if(MB < 1024) {
        str = (MB) + "MB"
    }
    else if(MB < 1024*1024) {
        str = (MB/1024.0) + "GB";
    }
    else {
        str = (MB/(1024*1024.0)) + "TB"; 
    }

    return str;
}

function _MB_to_slide(MB, zeroVal){
    var slide;
    
    if(MB == 0) {
        slide = zeroVal;
    }
    else if(MB < 1024) {   
        slide = Math.log(MB)/Math.log(2);
    }
    else {
        slide = MB/1024 + 9
    }

    return Math.floor(slide);
}

function _slide_to_MB(slide, slideMin, mbMin, slideMax, mbMax){
    var MB;

    if(slide == slideMin) {
        MB = mbMin;
    }
    else if(slide < 10) {
        MB = Math.pow(2, slide);
    }
    else {
        MB = ((slide - 9) * 1024);
    }

    return MB;
}

function _normalize_string(str, mbMin, mbMax){
    var normString = '';
    var value = _string_to_MB(str);
   
    if(value < mbMin) {
        value = mbMin;
    }
    else if(value > mbMax) {
        value = mbMax;
    }
    
    if(value < 1024) {
        normString = value + "MB";
    }
    else if(value < 1024*1024) {
        normString = value/1024 + "GB";
    }
    else {
        normString = value/(1024*1024) + "TB";
    }
    
    return normString;
}


/************
_adjust_sliders accepts a slider, MB value, textbox, and groupMaster.

It then adjusts the values and positions of all other sliders in the group,
and sets the texbox to the new value.

groupMaster is any jquery object that can be accessed by every slider in
this group. It is used to store coordinate the groupMax and groupName.
Typically this is assumed to be the textbox that corresponds to the first 
slider in this group. 
*************/
function _adjust_sliders(currentSlider, newMB, textbox, groupMaster){
    var min = currentSlider.slider("option", "min");
    var prevMB = currentSlider.slider("option", "mbvalue");
    var maxChange = parseInt(newMB - prevMB);

    groupMaster.data("groupmax", (groupMaster.data("groupmax") - maxChange));
    var className = groupMaster.data("groupname");

    // Adjust the max values of all other sliders in this group, 
    // then update their values accordingly.
    $("."+className).each(function(index){
        // handle all sliders other than the one triggering this event
        if(currentSlider.attr("id") != $(this).attr("id")) { 
            var thisMax = $(this).slider("option", "max");
            var thisMbmax = $(this).slider("option", "mbmax");
            var thisMbmin = $(this).slider("option", "mbmin");
            var thisMin = $(this).slider("option", "min");
            var thisMbvalue = $(this).slider("option", "mbvalue");
            var newMbmax = thisMbmax - maxChange;
            $(this).slider("option", "mbmax", newMbmax );
            $(this).slider("option", "max", _MB_to_slide(newMbmax, thisMin));
            
            if( _MB_to_slide(prevMB, thisMin) != _MB_to_slide(newMB, thisMin) ) {
                // only move the slider if it needs to move
                $(this).slider("value", $(this).slider("value"));   
            }
        }
    });

    textbox.val(_MB_to_string(newMB));
    currentSlider.slider("option","mbvalue",newMB);
}



/************
initSlider takes a textbox, an object to designate as the groupMaster,
a MB value to set as the groupMax (if groupMaster is not already initialized),
and a class name to be used by all sliders in this group (if not already set).
All parameters are required, but the last two are not used unless this is the
first slider in its group.

A new slider will be created under the specified textbox, tied to the other
sliders that share the specified groupMaster object. A new change event handler
will be bound to the provided textbox in order to incorporate its values.

groupMaster is any jquery object that can be accessed by every slider in
this group. It is used to store coordinate the groupMax and groupName.
Typically this is assumed to be the textbox that corresponds to the first 
slider in this group. 
*************/
function initSlider(textbox, groupMaster, groupMax, groupName) {   
    if (!groupMaster.data("groupmax")) {
        groupMaster.data("groupmax", groupMax);
        groupMaster.data("groupname", groupName);
    }

    var name = textbox.attr("id");
    var className = groupMaster.data("groupname");
    var sliderObject = $('<object></object>');
    var sliderDiv = $('<div></div>');
    sliderDiv.attr("id",name+"_slider");
    sliderDiv.attr("class",className);
    sliderObject.append(sliderDiv);
    textbox.parent().append(sliderObject);
    var slider = $("#"+name+"_slider");

    // Resize the parent if needed to prevent overlapping with other elements
    if (textbox.parent().height() < textbox.height()) {
        textbox.parent().height(textbox.parent().height() + textbox.height()*2);
    }

    slider.width(textbox.width()).offset({
        top: (textbox.offset().top + textbox.height()*1.5), left: textbox.offset().left})
    .slider({
        mbmin: 0,
        mbmax: groupMaster.data("groupmax"),
        min: -1,
        max: _MB_to_slide(groupMaster.data("groupmax"), -1),
        value: -1,
        mbvalue: 0
    }).bind("slide slidechange", function( event, ui ){
        var min = $(this).slider("option","min");
        var mbmin = $(this).slider("option", "mbmin");
        var max = $(this).slider("option", "max");
        var mbmax = $(this).slider("option", "mbmax");
        var prevMB = $(this).slider("option", "mbvalue"); 
        var newMB = _slide_to_MB(ui.value, min, mbmin, max, mbmax);
        var maxChange = newMB - prevMB;
        
        
        if( _MB_to_slide(prevMB, min) != _MB_to_slide(newMB, min) ) { 
            // if this slider has changed value, change the max values of its group
            _adjust_sliders($(this), newMB, textbox, groupMaster);
        }
        
    });
    
    textbox.bind("change", function(){
        var mbMin = $("#"+name+"_slider").slider("option","mbmin");
        var mbMax = $("#"+name+"_slider").slider("option","mbmax");
        var prevMB = $("#"+name+"_slider").slider("option","mbvalue");
        
        textbox.val(_normalize_string(textbox.val(), mbMin, mbMax));
        
        var value = textbox.val();
        var newMB = _string_to_MB(value);
        slider.slider("value", _string_to_slide(value, slider.slider("option","min")));
        _adjust_sliders($("#"+name+"_slider"), newMB, textbox, groupMaster);    
        
        textbox.val(value);
    });

    // If the textbox had a previous value, handle that value as a change
    // in order to update groupMax and the values of all the sliders.
    if (textbox.val()) {
        textbox.change();
    }

    slider.css( "background-color", "#111199");
    slider.css( "padding", "30px, 30px, 30px, 30px");
    slider.css( "overflow", "visible");
}



/************
removeSlider takes a textbox and the groupMaster object for this group.

The slider associated with this textbox will be removed, and its value
(if any) will be returned to the groupMax and all other sliders in the group.

groupMaster is any jquery object that can be accessed by every slider in
this group. It is used to store coordinate the groupMax and groupName.
Typically this is assumed to be the textbox that corresponds to the first 
slider in this group. 
*************/
function removeSlider(textbox, groupMaster) {   
    var className = groupMaster.data("groupname");
    $("."+className).each(function(index){
        var thisMax = $(this).slider("option", "max");
        var thisMbmax = $(this).slider("option", "mbmax");
        var thisMbmin = $(this).slider("option", "mbmin");
        var thisMin = $(this).slider("option", "min");
        var thisMbvalue = $(this).slider("option", "mbvalue");
        var newMbmax = parseInt(thisMbmax) + parseInt(_string_to_MB(textbox.val()));
        $(this).slider("option", "mbmax", newMbmax );
        $(this).slider("option", "max", _MB_to_slide(newMbmax, thisMin));
    });
   
    groupMaster.data("groupmax", 
        (parseInt(groupMaster.data("groupmax")) 
        + parseInt(_string_to_MB(textbox.val()))));
}

