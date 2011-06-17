/*
 * jQuery Progress Bar plugin
 * Version 2.0 (06/22/2009)
 * @requires jQuery v1.2.1 or later
 *
 * Copyright (c) 2008 Gary Teo
 * http://t.wits.sg

USAGE:
    $(".someclass").progressBar();
    $("#progressbar").progressBar();

    // percentage
    $("#progressbar").progressBar(45);

    // percentage with config
    $("#progressbar").progressBar({showText: false });

    // percentage with config
    $("#progressbar").progressBar(45, {showText: false });
*/
(function($) {
    $.extend({
        progressBar: new function() {
            this.defaults = {
                // steps taken to reach target
                steps: 20,
                stepDuration: 20,
                // Upon 100% i'd assume, but configurable
                max: 100,
                /* Show text with percentage in next to
                   the progressbar. - default : true */
                showText: true,
                // Or otherwise, set to 'fraction'
                textFormat: 'percentage',
                /* Width of the progressbar
                   don't forget to adjust your
                   image too!!! */
                width: 120,
                /* Height of the progressbar
                   Don't forget to adjust your image too! */
                height: 12,
                /* Calls back with the config object that has
                   the current percentage, target percentage,
                   current image, etc */
                callback: null,
                // boxImage : image around the progress bar
                boxImage: 'images/progressbar.gif',
                /* Image to use in the progressbar.
                   Can be a single image too:
                   'images/progressbg_green.gif' */
                barImage: {
                    0:'images/progressbg_red.gif',
                    30:'images/progressbg_orange.gif',
                    70:'images/progressbg_green.gif'
                },
                // Internal use
                running_value: 0,
                value: 0,
                image: null
            };

            /* public methods */
            this.construct = function(arg1, arg2) {
                var argvalue = null;
                var argconfig = null;

                if (arg1 != null) {
                    if (!isNaN(arg1)) {
                        argvalue = arg1;
                        if (arg2 != null) {
                            argconfig = arg2;
                        }
                    } else {
                        argconfig = arg1;
                    }
                }

                return this.each(function(child) {
                    var pb = this;
                    var config = this.config;

                    if (argvalue != null && this.bar != null && this.config != null) {
                        this.config.value = argvalue
                        if (argconfig != null)
                            pb.config = $.extend(this.config, argconfig);
                        config = pb.config;
                    } else {
                        var $this = $(this);
                        var config = $.extend({}, $.progressBar.defaults, argconfig);
                        config.id = $this.attr('id') ? $this.attr('id') : Math.ceil(Math.random() * 100000);  // random id, if none provided
                        if (config.textFormat == 'percentage'){
                            // parse percentage
                            argvalue = $this.html().replace("%","");
                        }
                        else if (config.textFormat == 'fraction'){
                            try{
                                var parts = $this.html().split('/');
                                argvalue = parts[0].replace(' ', '');
                                config.max = parts[1].replace(' ', '');
                            }
                            catch(e){
                                argvalue = 0;
                                config.max = 0;
                            }
                        }
                        config.value = argvalue;
                        config.running_value = 0;
                        config.image = getBarImage(config);

                        $this.html("");
                        var bar = document.createElement('img');
                        var text = document.createElement('span');
                        var $bar = $(bar);
                        var $text = $(text);
                        pb.bar = $bar;

                        $bar.attr('id', config.id + "_pbImage");
                        $text.attr('id', config.id + "_pbText");
                        $text.html(getText(config));
                        $bar.attr('title', getText(config));
                        $bar.attr('alt', getText(config));
                        $bar.attr('src', config.boxImage);
                        $bar.attr('width', config.width);
                        $bar.css("width", config.width + "px");
                        $bar.css("height", config.height + "px");
                        $bar.css("background-image", "url(" + config.image + ")");
                        $bar.css("background-position", ((config.width * -1)) + 'px 50%');
                        $bar.css("padding", "0");
                        $bar.css("margin", "0");
                        $this.append($bar);
                        $this.append($text);
                    }

                    function getPercentage(config) {
                        var percent = (config.running_value * 100 / config.max);
                        if (percent > 100) {
                            return 100;
                        }
                        return percent;
                    }

                    function getBarImage(config) {
                        var image = config.barImage;
                        if (typeof(config.barImage) == 'object') {
                            for (var i in config.barImage) {
                                if (getPercentage(config) >= parseInt(i)) {
                                    image = config.barImage[i];
                                } else { break; }
                            }
                        }
                        return image;
                    }

                    function getText(config) {
                        if (config.showText) {
                            if (config.textFormat == 'percentage') {
                                return " " + Math.round(config.running_value) + "%";
                            } else if (config.textFormat == 'fraction') {
                                return " " + config.running_value + ' / ' + config.max;
                            }
                        }
                    }

                    config.increment = Math.round((config.value - config.running_value)/config.steps);
                    if (config.increment < 0)
                        config.increment *= -1;
                    if (config.increment < 1)
                        config.increment = 1;

                    var t = setInterval(function() {
                        // Define how many pixels go into 1%
                        var pixels  = config.width / 100;
                        if (config.running_value > config.value) {
                            if (config.running_value - config.increment  < config.value) {
                                config.running_value = config.value;
                            } else {
                                config.running_value -= config.increment;
                            }
                        } else if (config.running_value < config.value) {
                            if (config.running_value + config.increment  > config.value) {
                                config.running_value = config.value;
                            } else {
                                config.running_value += config.increment;
                            }
                        }
                        if (config.running_value == config.value)
                            clearInterval(t);
                        var $bar    = $("#" + config.id + "_pbImage");
                        var $text   = $("#" + config.id + "_pbText");
                        var image   = getBarImage(config);

                        if (image != config.image) {
                            $bar.css("background-image", "url(" + image + ")");
                            config.image = image;
                        }
                        $bar.css("background-position", (((config.width * -1)) + (getPercentage(config) * pixels)) + 'px 50%');
                        $bar.attr('title', getText(config));
                        $text.html(getText(config));
                        if (config.callback != null && typeof(config.callback) == 'function')
                            config.callback(config);
                        pb.config = config;
                    }, config.stepDuration);
                });
            };
        }
    });
    $.fn.extend({
        progressBar: $.progressBar.construct
    });
})(jQuery);
