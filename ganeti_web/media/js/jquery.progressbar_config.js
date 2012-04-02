
/*
 * jQuery Progress Bar Config Plugin
 *
 * This is a plugin for generating a configuration that can be used in
 * with the jQuery ProgressBar plugin.  This generates an intuitive widget for
 * choosing where color ranges start/end.
 *
 * Copyright (c) 2011 Open Source Lab

*/
(function($) {
	$.extend({
		progressBarConfig: new function() {

			this.defaults = {
                'width': 400,
			    'colors': [
                        ['green',0],
                        ['yellow',50],
                        ['orange',60],
                        ['red',75]]
			};

			/* public methods */
			this.construct = function(arg1) {
				var arg_config	= null;

				if (arg1 != null) {
					arg_config = arg1;
				}

				return this.each(function() {
					var control = this;
                    var input = $(this);
                    var config = undefined;

                    // create configuration
                    if (arg_config==null) {
                        config = $.extend({}, $.progressBarConfig.defaults, arg_config);
                    } else {
                        config = $.extend(this.config, arg_config);
                    }
                    if (input.val() != '') {
                        config.colors =  $.parseJSON(input.val());
                    }

                    //get config values
                    var colors = config.colors;
                    var width = config.width;
                    var slider = undefined;

                    this._init = function() {
                        // Process color information, also resize divs to fit the slider.
                        slider = $("<div class='slider'></div>");
                        for (var i in colors){
                            i = parseInt(i);
                            var div = $("<div class='section'></div>");
                            var color = colors[i][0];
                            var start = colors[i][1];

                            div.attr('id',color);

                            if (i < colors.length-1) {
                                div.append("<div class='handle right'></div>");
                                div.width((colors[i+1][1]-start)/100*width);
                            } else {
                                div.width((100-start)/100*width);
                            }

                            if (i > 0) {
                                div.append("<div class='handle left'></div>");
                            }
                            slider.append(div);
                        }

                        slider.find('.handle').mousedown(control._mousedown);
                        input.hide();
                        input.after(slider);
                    };

                    var origin = undefined;
                    var moving = undefined;
                    var other = undefined;
                    var moving_origin = undefined;
                    var other_origin = undefined;
                    var reverse = undefined;

                    control._mousedown = function(event){
                        var bound = $(this);
                        origin = event.pageX;
                        moving = bound.parent();
                        if (bound.hasClass('left')) {
                            other = moving.prev();
                            reverse = true;
                        } else {
                            other = moving.next();
                            reverse = false;
                        }
                        moving_origin = moving.width();
                        other_origin = other.width();

                        $('html')
                            .mouseup(control._mouseup)
                            .mousemove(control._slide_react);
                    };

                    control._mouseup = function(event) {
                        event.preventDefault();
                        slider.unbind('mousemove');
                        origin = undefined;
                        moving = undefined;
                        other = undefined;
                        $('html')
                            .unbind('mouseup')
                            .unbind('mousemove');

                        // process bar sizes
                        // XXX no JSON encoder so just manually encode array
                        var sections = slider.find('.section');
                        var data = "[";
                        var acc = 0;
                        for (var i in colors) {
                            if (i!=0) {
                                data += ",";
                            }
                            data += '["' + [colors[i][0]] + '",' + acc + ']';
                            acc += $(sections[i]).width()/width*100;
                        }
                        data += "]";
                        input.val(data);
                    };

                    this._slide_react = function(event) {
                        var offset = event.pageX - origin;

                        if (reverse) {
                            if (offset > 1 && moving_origin-offset < 0) {
                                offset = moving_origin;
                            } else if (other_origin+offset < 0) {
                                offset = -1*other_origin;
                            }
                            moving.width(moving_origin-offset);
                            other.width(other_origin+offset);
                        } else {
                            if (offset > 1 && other_origin-offset < 0) {
                                offset = other_origin;
                            } else if (moving_origin+offset < 0) {
                                offset = -1*moving_origin;
                            }
                            moving.width(moving_origin+offset);
                            other.width(other_origin-offset);
                        }
                    };

                    this._init();
				});
			};
		}
    });

	$.fn.extend({
        progressBarConfig: $.progressBarConfig.construct
	});

})(jQuery);
