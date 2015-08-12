(function () {

var hawkeye= {
    Main : Main,
    ShowChart : ShowChart,
};

window.hawkeye = hawkeye;

function initJSTree() {
    jQuery('#left-pane').on('changed.jstree', function (e, data) {
        var node, value, parent_value, i, j, r = [], pr = [];
        for(i = 0, j = data.selected.length; i < j; i++) {
            node = data.instance.get_node(data.selected[i]);
            r.push(node.text);
            pr.push(data.instance.get_node(data.instance.get_parent(node)).text);
        }
        value = r.join(', ').trim();
        parent_value = pr.join(', ').trim();
        console.log(value + ' ' + parent_value);

        if (parent_value === 'Resource') {
            jQuery('#resource-type').html(value);
            
        } else if (parent_value === 'Dimension' || parent_value === 'Process') {
            if (value !== 'Process') {
                jQuery('#dimension-type').html(value);
            }
        }
    }).jstree();

    jQuery('#left-pane').jstree().open_all(null, 3000);
}

function Main() {
    initJSTree();
}

function ShowChart() {
    var hostBeginId = jQuery('#host-id-begin').val();
    var hostEndId = jQuery('#host-id-end').val();
    var hostGroupSize = jQuery('#host-group').val();

    var timeBegin = jQuery('#time-begin').val();
    var timeEnd = jQuery('#time-end').val();
    var timeInterval = jQuery('#time-interval').val();
    
    var resType = jQuery('#resource-type').text();
    var measureType = jQuery('#measure-type-select').val();
    var dimType = jQuery('#dimension-type').text();

    jQuery.ajax({ type : "GET",
            url: "rest",
            data: "resType="+resType+"&measureType="+measureType+"&dimType="+dimType+"&hostBeginId="+hostBeginId+"&hostEndId="+hostEndId+"&hostGroupSize="+hostGroupSize+"&timeBegin="+timeBegin+"&timeEnd="+timeEnd+"&timeInterval="+timeInterval,
            contentType: "application/json",
            success: function(data) {
                ShowChartCallback(data);
            },
            error: function(response, textStatus, errorThrown) {
                console.log(errorThrown + " - " + response.responseText);
            },
    });  
}

function ShowChartCallback(data) {
    var data = JSON.parse(data);

    var x = data.x;
    var y = data.y; 

    var chartType = jQuery('#chart-type-select').val();
    var groupSize = parseInt(jQuery('#host-group').val());
    var measureType = jQuery('#measure-type-select').val();

    var title = jQuery('#resource-type').text();
    if (title !== 'CPU') {
        title = title + " (MB)";
    }

    var xData = x;
    var yData = new Array(y.length);
    var yName = [];
    var i, j; 

    for (i=0;i<yData.length;i++) {
        yData[i] = {};
        yData[i].name = y[i][0];
        yData[i].data = y[i][1];
    }
    
    console.log(x)
    console.log(xData);
    console.log(y)
    console.log(yData);

    /*
     *  Set chart-by-time-select
     */
    var timeSelect = jQuery('#chart-by-time-select');
    timeSelect.empty();

    timeSelect.append(jQuery("<option>").val("").text("")); 
    for (i=0;i<xData.length;i++) {
        var optionValue = [];
        for (j=0;j<yData.length;j++) {
            optionValue.push(yData[j]['name']);
            optionValue.push(yData[j]['data'][i]);
        }

        option = jQuery("<option>").val(optionValue.join(',')).text(xData[i]);
        timeSelect.append(option);
    }
    timeSelect.change(function() {
        var zData = [];
        var data = jQuery('#chart-by-time-select').val().split(',');
        var zTitle = jQuery('#chart-by-time-select').find("option:selected").text();
        if (data.length == 0) {
            return;
        }
        for (i=0;i<data.length;i+=2) {
            zData.push([data[i], parseFloat(data[i+1])]); 
        }
        GenPieChart(zTitle, zData);
    });

    GenChart(chartType, title, xData, yData);
}

function GenPieChart(title, zData) {
    jQuery('#chart').highcharts({
            chart: {
                type: 'pie',
            }, 

            title: {
                text: title,
            },
            
            tooltip: {
                //pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
            },
            plotOptions: {
              pie: {
                  allowPointSelect: true,
                  cursor: 'pointer',
                  dataLabels: {
                      enabled: true,
                            format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                      style: {
                          color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                      }
                  },
                showInLegend: true
              }
          },

            credits: {
                enabled: true,        
                text: 'Design By BMW'
            },
            series: [{
                name: title,
                data: zData
            }]
    });
}


function GenChart(chartType, title, xData, yData) {

    jQuery('#chart').highcharts({
            chart: {
                type: chartType,
            }, 

            title: {
                text: title,
                x: -20
            },
            xAxis: {
                title: {
                    text: 'Time'
                },

                categories: xData
            },
            yAxis: {
                title: {
                    text: title
                },
            },
            
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                borderWidth: 1
            },
            credits: {
                enabled: true,        
                text: 'Design By BMW'
            },
            series: yData
    });
}

}());
