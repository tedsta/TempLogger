$(document).foundation();

// socket.io specific code
var socket = io.connect();

$(window).bind("beforeunload", function() {
    socket.disconnect();
});

socket.on('connect', function () {
    //$('#chat').addClass('connected');
});

socket.on('error', function (e) {
});

socket.on('data_tables', on_data_tables);
socket.on('data_plot', on_data_plot);
socket.on('degree_days', on_degree_days);
socket.on('degree_days_error', on_degree_days_error);

function on_data_tables(file_list) {
    $("#data-tables-list").empty()
    for (var i = 0; i < file_list.length; i++) {
        $("#data-tables-list").append("<li><a href=\""+file_list[i][0]+"\">"+file_list[i][1]+"</a></li>")
    }
}

function on_data_plot(plot_file) {
    $("#data-plot-holder").empty()
    $("#data-plot-holder").append("<img src=\""+plot_file+"\" alt=\"data plot\" />")
}

function on_degree_days(deg_days) {
    $('#degree-days').text(deg_days);
}

function on_degree_days_error(msg) {
    $("<div data-alert class=\"alert-box alert radius\">"+msg+"<a href=\"#\" class=\"close\">&times;</a></div>").insertAfter($("#degree-days-separator"))
    $(document).foundation();
}

// DOM manipulation
$(function () {
    $('#data-tables').submit(function (ev) {
        socket.emit('data_tables', $('#data-tables-start').val(), $('#data-tables-end').val());
        return false;
    });
    $('#data-plots').submit(function (ev) {
        socket.emit('data_plot', $('#data-plots-date').val());
        return false;
    });
    $('#degree-days-calculator').submit(function (ev) {
        ambient_probe = ($('#ambient-probe').is(':checked')) ? "probe" : "ambient";
        socket.emit('get_degree_days', $('#base-temp').val(), ambient_probe, $('#degree-days-start').val(), $('#degree-days-end').val());
        return false;
    });
});
