(function( $ ){

    $.fn.dualMeter = function(options, secondaryOptions) {

	    var defaults = {
            // Primary percentage
            'primary': '50',
            // Secondary percentage
            'secondary': '50',
            // All divs height
            'height': '12',
            // Outer div width
            'width': '123',
            // Outer div background image
            'bgImage': 'images/meter_bg.png',
            // The meter bar images for the inner divs
            'progBarImages': {
                0:  ['images/meter_green.png',
                     'images/meter_green_dark.png'],
                25: ['images/meter_yellow.png',
                     'images/meter_yellow_dark.png'],
                50: ['images/meter_orange.png',
                     'images/meter_orange_dark.png'],
                75: ['images/meter_red.png',
                     'images/meter_red_dark.png']
            }
        }

        settings = $.extend(defaults, options, secondaryOptions);
	

        // Grab the first set of images as default, then,
        // check the percentage given for the primary value
        // and change the image set based on it's percentage.
        function getImages(settings) {
            var images = settings.progBarImages[0];
            for (var i in settings.progBarImages) {
                if (settings.primary >= parseInt(i)) {
                    images = settings.progBarImages[i];
                } else { break; }
            }
            return images;
        }

        return this.each(function() {

            // $this-ing for jQuery chainability
            var $this = $(this);

            // Percentage of settings.width for meter bar in pixels
            var primaryW = (settings.primary / 100) * settings.width;
            var secondaryW = (settings.secondary / 100) * settings.width;
            var imgs = getImages(settings);

            // Correct for negative values
            primaryW < 0 ? primaryW = 0 : primaryW = primaryW;
            secondaryW < 0 ? secondaryW = 0 : secondaryW = secondaryW;

            // if primary is larger than the width of the full bar
            // set primary to 100% and the secondary to 0%
            if (primaryW > settings.width) {
                primaryW = settings.width;
                secondaryW = 0;
            }

            // If primary and secondary are larger than settings.width and primary
            // is less than settings.width, shrink secondary to fit
            if ((primaryW + secondaryW) > settings.width) {
                secondaryW = settings.width - primaryW;
            }

            // Predefine some CSS
            var halfHeight = (settings.height / 2);
            var $resetCSS = {
                'border':'0px',
                'padding':'0px',
                'margin':'auto',
                'height':settings.height + 'px'
            }
            var $primCSS =  {
                'float':'left',
                'width':primaryW + 'px',
                'background-image':"url('" + imgs[0] + "')",
        		'background-repeat':'repeat-x',
        		'border-top-left-radius':halfHeight + 'px',
        		'border-bottom-left-radius':halfHeight + 'px',
            }
            var $secndCSS = {
                'float':'left',
                'width':secondaryW + 'px',
                'background-image':"url('" + imgs[1] + "')",
        		'border-top-right-radius':halfHeight + 'px',
        		'border-bottom-right-radius':halfHeight + 'px',
            }

            // Give the primary meter a right rounded border if secondary
            // is 0 or less.
            if (settings.secondary <= 0) {
                $primCSS['border-top-right-radius'] = halfHeight + 'px';
                $primCSS['border-bottom-right-radius'] = halfHeight + 'px';
            }

            // Give the secondary meter a left rounded border if primary
            // is 0 or less.
            if (settings.primary <= 0) {
                $secndCSS['border-top-left-radius'] = halfHeight + 'px';
                $secndCSS['border-bottom-left-radius'] = halfHeight + 'px';
            }
            
            // Setup the size of the div
            $this.css($resetCSS).css('width',settings.width + 'px');
            $this.css('background-image','url("' + settings.bgImage + '")');
            var $prim = $(document.createElement('div'));
            $prim.css($resetCSS).css($primCSS);
            var $secnd = $(document.createElement('div'));
            $secnd.css($resetCSS).css($secndCSS);

            // Append the primary and secondary divs to the progress bar
            $(this).append($prim);
            $(this).append($secnd);
    });
  };
})( jQuery );
