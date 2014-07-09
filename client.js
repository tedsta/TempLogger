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
socket.on('degree_days', on_degree_days);

function on_data_tables(file_list) {
    $("#data-plots-list").empty()
    for (var i = 0; i < file_list.length; i++) {
        $("#data-plots-list").append("<li><a href=\""+file_list[i][0]+"\">"+file_list[i][1]+"</a></li>")
    }
}

function on_degree_days(deg_days) {
    $('#degree-days').text(deg_days);
}

// DOM manipulation
$(function () {
    $('#data-tables').submit(function (ev) {
        socket.emit('data_tables', $('#data-tables-start').val(), $('#data-tables-end').val());
        return false;
    });
    $('#degree-days-calculator').submit(function (ev) {
        ambient_probe = ($('#ambient-probe').is(':checked')) ? "probe" : "ambient";
        socket.emit('get_degree_days', $('#base-temp').val(), ambient_probe, $('#degree-days-start').val(), $('#degree-days-end').val());
        return false;
    });
});
