/*------------------------------------------------------
    Author : www.webthemez.com
    License: Commons Attribution 3.0
    http://creativecommons.org/licenses/by/3.0/
---------------------------------------------------------  */

$(document).ready((function ($) {
    google.charts.load('current', {'packages': ['gantt'], 'language': 'ru'});

    "use strict";
    var mainApp = {

        initFunction: function () {
            /*MENU 
            ------------------------------------*/
            // $('#main-menu').metisMenu();

            $(window).bind("load resize", function () {
                if ($(this).width() < 768) {
                    $('div.sidebar-collapse').addClass('collapse')
                } else {
                    $('div.sidebar-collapse').removeClass('collapse')
                }
            });


            /* MORRIS BAR CHART
			-----------------------------------------*/
            if ($('*').is('#url_ajax_chart_bar')) {
                try {
                    $.ajax({
                        url: $("#url_ajax_chart_bar").attr('url_ajax_chart_bar'),
                        dataType: 'json',
                        success: function (data) {
                            Morris.Bar({
                                element: 'morris-bar-chart',
                                data: data,
                                stacked: true,
                                xkey: 'y',
                                ykeys: ['a', 'b'],
                                labels: ['Выполненно', 'Создано'],
                                barColors: [
                                    '#e96562', '#414e63',
                                    '#A8E9DC'
                                ],
                                hideHover: 'auto',
                                resize: true
                            });
                        }
                    })
                }
                catch (err) {
                }
            }

            /* MORRIS DONUT CHART
			----------------------------------------*/

            /* MORRIS LINE CHART
----------------------------------------*/
            if ($('*').is('#url_ajax_line_chart')) {
                try {
                    $.ajax({
                        url: $("#url_ajax_line_chart").attr('url_ajax_line_chart'),
                        dataType: 'json',
                        success: function (data) {
                            Morris.Line({
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
                                pointFillColors: ['#ffffff'],
                                pointStrokeColors: ['black'],
                                lineColors: ['gray']

                            });
                        }
                    })
                }
                catch (err) {
                }
            }

            $('.bar-chart').cssCharts({type: "bar"});
            $('.donut-chart').cssCharts({type: "donut"}).trigger('show-donut-chart');
            $('.line-chart').cssCharts({type: "line"});

        },

        initialization: function () {
            mainApp.initFunction();

        }

    }
    // Initializing ///

    $(document).ready(function () {
        $(".dropdown-button").dropdown();
        $("#sideNav").click(function () {
            if ($(this).hasClass('closed')) {
                $('.navbar-side').animate({left: '0px'});
                $(this).removeClass('closed');
                $('#page-wrapper').animate({'margin-left': '260px'});

            }
            else {
                $(this).addClass('closed');
                $('.navbar-side').animate({left: '-260px'});
                $('#page-wrapper').animate({'margin-left': '0px'});
            }
        });

        mainApp.initFunction();
    });

    $(".dropdown-button").dropdown();

}(jQuery)));


function DonutChart() {
    $("#morris-donut-chart").empty()
    if ($('*').is('#url_ajax_chart')) {
        try {
            $.ajax({
                url: $("#url_ajax_chart").attr('url_ajax_chart'),
                dataType: 'json',
                success: function (data) {
                    Morris.Donut({
                        element: 'morris-donut-chart',
                        data: data,
                        colors: [
                            '#A6A6A6', '#414e63',
                            '#e96562'
                        ],
                        resize: true,
                        height: '500px'
                    });
                }
            })
        }
        catch (err) {
        }
    }
}

function drawChartGantt(url) {
    var jsonData = $.ajax({
        url: url,
        dataType: "json",
        async: false
    }).responseText;
    var my_data = JSON.parse(jsonData);
    var data = new google.visualization.DataTable();
    $.each(my_data.cols, function (index, value) {
        data.addColumn(value["type"], value["label"]);
    });
    var rows = [];
    $.each(my_data.rows, function (index, value) {
        var row = []
        $.each(value, function (index, value) {
            if (index === 3 || index === 4) {
                row.push(new Date(value))
            }
            if (index === 0) {
                row.push(String(value))
            }
            if (index === 1 || index === 2) {
                row.push(value)
            }
            if (index === 5 || index === 6) {
                row.push(Number(value))
            }
            if (index === 7) {
                row.push(value)
            }
        });
        rows.push(row)
    });
    data.addRows(rows);
    var options = {
        height: rows.length * 30,
        width: $('#Gantt').width() * 1,
        // gantt: {
        //     defaultStartDateMillis: new Date(2015, 3, 28)
        // }
        criticalPathStyle: {
            stroke: '#e64a19',
            strokeWidth: 5
        },
        gantt: {
            trackHeight: 30
        }
    };

    var chart = new google.visualization.Gantt(document.getElementById('chart_div'));

    function selectHandler() {
        var selections = chart.getSelection();
        if (selections.length == 0) {
            // alert('Nothing selected');
        } else {
            var selection = selections[0];
            console.info(selection);
            TaskDetail('/task/det/'+data.getValue(selection.row, 0)+'/')
        }
    }

    google.visualization.events.addListener(chart, 'select', selectHandler);

    chart.draw(data, options);

}

function drawBurndownChart(url) {
    var jsonData = $.ajax({
        url: url,
        dataType: "json",
        async: false
    }).responseText;
    var my_data = JSON.parse(jsonData);
    google.charts.load('current', {'packages':['line'], 'language': 'ru'});
    google.charts.setOnLoadCallback(drawChart);

    function drawChart() {

      var data = new google.visualization.DataTable();
      data.addColumn('number', 'Дни');
      data.addColumn('number', 'Идеальная линия выполнения задач, на которую и следует опираться');
      data.addColumn('number', 'Реальная история выполнения   задач');


    data.addRows(my_data);
      // data.addRows([
      //   [14,  12, 14],
      //   [13,  18, 16],
      //   [12,  24,   25],
      //   [11,  30, 28],
      //   [10,  36, 35],
      //   [9,   42, 40],
      //   [8,   48, 52],
      //   [7,  54, 50],
      //   [6,  60, 60],
      //   [5, 66, 68],
      //   [4,  72,  75],
      //   [3,  78,  74],
      //   [2,  84,  85],
      //   [1,  90,  90]
      // ]);

      var options = {
        chart: {
          title: 'Диаграмма сгорания задач',
          subtitle: 'Данный график является основным средством для отслеживания выполненных задач в спринте или во всем проекте'
        },
        // width: $('#burndown_chart').width() * 1,
        height: 500
      };

      var chart = new google.charts.Line(document.getElementById('burndown_chart'));

      chart.draw(data, google.charts.Line.convertOptions(options));
    }
    
}


$('#Gantt').resize(function () {
    chart.draw(data, options);
});
