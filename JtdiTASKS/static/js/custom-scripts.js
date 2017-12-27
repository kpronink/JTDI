/*------------------------------------------------------
    Author : www.webthemez.com
    License: Commons Attribution 3.0
    http://creativecommons.org/licenses/by/3.0/
---------------------------------------------------------  */

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
    // google.charts.load('current', {'packages': ['gantt']});
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
        height: rows.length * 32,
        width: $('#Gantt').width() * 1,
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
            TaskDetail('/task/det/' + data.getValue(selection.row, 0) + '/')
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
    // google.charts.load('current', {'packages': ['line'], 'language': 'ru'});

    var data = new google.visualization.DataTable();
    data.addColumn('number', 'Дни');
    data.addColumn('number', 'Идеальная линия выполнения задач, на которую и следует опираться');
    data.addColumn('number', 'Реальная история выполнения   задач');

    data.addRows(my_data);

    var options = {
        chart: {
            title: 'Диаграмма сгорания задач',
            subtitle: 'Данный график является основным средством для отслеживания выполненных задач в спринте или во всем проекте'
        },
        height: 500
    };

    var chart = new google.charts.Line(document.getElementById('burndown_chart'));

    chart.draw(data, google.charts.Line.convertOptions(options));
    
}


$('#Gantt').resize(function () {
    chart.draw(data, options);
});
