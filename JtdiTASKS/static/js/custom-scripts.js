/*------------------------------------------------------
    Author : www.webthemez.com
    License: Commons Attribution 3.0
    http://creativecommons.org/licenses/by/3.0/
---------------------------------------------------------  */

(function ($) {
    "use strict";
    var mainApp = {

        initFunction: function () {
            /*MENU 
            ------------------------------------*/
            $('#main-menu').metisMenu();
			
            $(window).bind("load resize", function () {
                if ($(this).width() < 768) {
                    $('div.sidebar-collapse').addClass('collapse')
                } else {
                    $('div.sidebar-collapse').removeClass('collapse')
                }
            });


            /* MORRIS BAR CHART
			-----------------------------------------*/
            try{
            $.ajax({
                    url: $("#url_ajax_chart_bar").attr('url_ajax_chart_bar'),
                    dataType: 'json',
                    success: function (data){Morris.Bar({
                element: 'morris-bar-chart',
                data: data,
                xkey: 'y',
                ykeys: ['a', 'b'],
                labels: ['Создано', 'Выполненно'],
				 barColors: [
    '#e96562','#414e63',
    '#A8E9DC'
  ],
                hideHover: 'auto',
                resize: true
            });}})}
            catch(err)
{ }

            /* MORRIS DONUT CHART
			----------------------------------------*/
            try
            {
                $.ajax({
                    url: $("#url_ajax_chart").attr('url_ajax_chart'),
                    dataType: 'json',
                    success: function (data){
                    Morris.Donut({
                        element: 'morris-donut-chart',
                        data: data,
                       colors: [
        '#A6A6A6','#414e63',
        '#e96562'
      ],
                        resize: true
                    });}})}
                             catch(err) { }

                $('.bar-chart').cssCharts({type:"bar"});
                $('.donut-chart').cssCharts({type:"donut"}).trigger('show-donut-chart');

            },

            initialization: function () {
                mainApp.initFunction();

            }

    }
    // Initializing ///

    $(document).ready(function () {
		$(".dropdown-button").dropdown();
		$("#sideNav").click(function(){
			if($(this).hasClass('closed')){
				$('.navbar-side').animate({left: '0px'});
				$(this).removeClass('closed');
				$('#page-wrapper').animate({'margin-left' : '260px'});
				
			}
			else{
			    $(this).addClass('closed');
				$('.navbar-side').animate({left: '-260px'});
				$('#page-wrapper').animate({'margin-left' : '0px'}); 
			}
		});
		
        mainApp.initFunction(); 
    });

	$(".dropdown-button").dropdown();
	
}(jQuery));
