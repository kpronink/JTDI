/*------------------------------------------------------
    Author : www.webthemez.com
    License: Commons Attribution 3.0
    http://creativecommons.org/licenses/by/3.0/
---------------------------------------------------------  */

$(document).ready((function ($) {
    google.charts.load('current', {'packages':['gantt']});
    
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
            if($('*').is('#url_ajax_chart_bar')) {try{
            $.ajax({
                    url: $("#url_ajax_chart_bar").attr('url_ajax_chart_bar'),
                    dataType: 'json',
                    success: function (data){Morris.Bar({
                element: 'morris-bar-chart',
                data: data,
                stacked: true,
                xkey: 'y',
                ykeys: ['a', 'b'],
                labels: ['Выполненно', 'Создано'],
				barColors: [
    '#e96562','#414e63',
    '#A8E9DC'
  ],
                hideHover: 'auto',
                resize: true
            });}})}
            catch(err)
{ }}

            /* MORRIS DONUT CHART
			----------------------------------------*/

                        /* MORRIS LINE CHART
			----------------------------------------*/
            if($('*').is('#url_ajax_line_chart')) {try{$.ajax({
                    url: $("#url_ajax_line_chart").attr('url_ajax_line_chart'),
                    dataType: 'json',
                    success: function (data){Morris.Line({
                element: 'morris-line-chart',
                data: data,
                xkey: 'y',
                ykeys: ['a'],
                labels: ['Количество минут'],
                fillOpacity: 0.6,
                hideHover: 'auto',
                stacked: true,
                behaveLikeLine: true,
                resize: true,
                parseTime: false,
                pointFillColors:['#ffffff'],
                pointStrokeColors: ['black'],
                lineColors:['gray']

                    });}})}
            catch(err) { }}

                $('.bar-chart').cssCharts({type:"bar"});
                $('.donut-chart').cssCharts({type:"donut"}).trigger('show-donut-chart');
                $('.line-chart').cssCharts({type:"line"});

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
	
}(jQuery)));


function DonutChart() {
    $("#morris-donut-chart").empty()
    if($('*').is('#url_ajax_chart')) {try
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
                             catch(err) { }}
}


function toMilliseconds(minutes) {
      return minutes * 60 * 1000;
    }

function drawChartGantt() {

      var otherData = new google.visualization.DataTable();
      otherData.addColumn('string', 'Task ID');
      otherData.addColumn('string', 'Task Name');
      otherData.addColumn('string', 'Resource');
      otherData.addColumn('date', 'Start');
      otherData.addColumn('date', 'End');
      otherData.addColumn('number', 'Duration');
      otherData.addColumn('number', 'Percent Complete');
      otherData.addColumn('string', 'Dependencies');
    
      otherData.addRows([
        ['toTrain', 'Walk to train stop', 'walk', null, null, toMilliseconds(5), 100, null],
        ['music', 'Listen to music', 'music', null, null, toMilliseconds(70), 100, null],
        ['wait', 'Wait for train', 'wait', null, null, toMilliseconds(10), 100, 'toTrain'],
        ['train', 'Train ride', 'train', null, null, toMilliseconds(45), 75, 'wait'],
        ['toWork', 'Walk to work', 'walk', null, null, toMilliseconds(10), 0, 'train'],
        ['work', 'Sit down at desk', null, null, null, toMilliseconds(2), 0, 'toWork'],

      ]);

      var options = {
        height: 275,
          width: $('#Gantt').width() * 0.95,
        gantt: {
          defaultStartDateMillis: new Date(2015, 3, 28)
        }
      };

      var chart = new google.visualization.Gantt(document.getElementById('chart_div'));

      chart.draw(otherData, options);
    }

$('#Gantt').resize(function(){
    chart.draw(data, options);
});
