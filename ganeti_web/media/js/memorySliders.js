
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
    else { // zero or non-number entered, set slide to value corresponding to 0MB
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
    else { // zero or non-number entered, set slide to value corresponding to 0MB
        MB = 0;
    }
    console.log("Evaluting string '" + str + "' to be " + MB + "MB");
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

groupMaster should have a groupMax attribute, which holds the remaining MB 
for the group to use, and a groupName attribute for the class name of sliders
that share that groupMax.
*************/
function _adjust_sliders(currentSlider, newMB, textbox, groupMaster){
    //console.log("Sliding " + currentSlider.attr("id"));
    var min = currentSlider.slider("option", "min");
    var prevMB = currentSlider.slider("option", "mbvalue");
    var maxChange = newMB - prevMB;

    groupMaster.attr("groupmax", (groupMaster.attr("groupmax") - maxChange));
    var className = groupMaster.attr("groupname");


    // Adjust the max values of all other sliders in this group, then update their value accordingly
    $("."+className).each(function(index){
        if(currentSlider.attr("id") != $(this).attr("id")) { // handle all sliders other than the one triggering this event
            try {
                //console.log("Attempting things on slider " + $(this).attr("id"));        
                var thisMax = $(this).slider("option", "max");
                var thisMbmax = $(this).slider("option", "mbmax");
                var thisMbmin = $(this).slider("option", "mbmin");
                var thisMin = $(this).slider("option", "min");
                var thisMbvalue = $(this).slider("option", "mbvalue");
                var newMbmax = thisMbmax - maxChange;
                $(this).slider("option", "mbmax", newMbmax );
                $(this).slider("option", "max", _MB_to_slide(newMbmax, thisMin));
                
                if( _MB_to_slide(prevMB, thisMin) != _MB_to_slide(newMB, thisMin) ) {
                    $(this).slider("value", $(this).slider("value"));   // only move the slider if it needs to move
                }
            } catch(err) {
                console.log("Failed to do things on slider " + $(this).attr("id"));
            }
        }
    });

    textbox.val(_MB_to_string(newMB));
    currentSlider.slider("option","mbvalue",newMB);
    
}



/************
groupMaster should have a groupMax attribute, which holds the remaining MB 
for the group to use, and a groupName attribute for the class name of sliders
that share that groupMax.
*************/
function initSlider(textbox, groupMaster, groupMax, groupName) {   
    if (!groupMaster.attr("groupname")) {
        groupMaster.attr({groupname: groupName, groupmax: groupMax});
    }

    var name = textbox.attr("id");
    var className = groupMaster.attr("groupname");
    var sliderDiv = $('<div></div>');
    sliderDiv.attr("id",name+"_slider");
    sliderDiv.attr("class",className);
    textbox.parent().append(sliderDiv);
    textbox.parent().height(textbox.height()*2);
    var slider = $("#"+name+"_slider");

    
    slider.width(textbox.width()).offset({
        top: (textbox.offset().top + textbox.height()*1.5), left: textbox.offset().left})
    .slider({
        mbmin: 0,
        mbmax: groupMaster.attr("groupmax"),
        min: -1,
        max: _MB_to_slide(groupMaster.attr("groupmax"), -1),
        value: -1,
        mbvalue: 0
    }).bind("slide slidechange", function( event, ui ){
        var min = $(this).slider("option","min");
        var mbmin = $(this).slider("option", "mbmin");
        var max = $(this).slider("option", "max");
        var mbmax = $(this).slider("option", "mbmax");
        var prevMB = $(this).slider("option", "mbvalue"); //_string_to_MB(textbox.val());
        var newMB = _slide_to_MB(ui.value, min, mbmin, max, mbmax);
        var maxChange = newMB - prevMB;
        
        
        if( _MB_to_slide(prevMB, min) != _MB_to_slide(newMB, min) ) { 
        // if this slider has changed value, change the max values of its group
            //console.log("Preparing " + $(this).attr("id"));
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


    slider.css( "background-color", "#111199");
    slider.css( "padding", "30px, 30px, 30px, 30px");
    slider.css( "overflow", "visible");
}



/************
groupMaster should have a groupMax attribute, which holds the remaining MB 
for the group to use, and a groupName attribute for the class name of sliders
that share that groupMax.
*************/
function removeSlider(textbox, groupMaster) {   
    var className = groupMaster.attr("groupname");
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
   
    groupMaster.attr("groupmax", (parseInt(groupMaster.attr("groupmax")) + parseInt(_string_to_MB(textbox.val()))));

}
