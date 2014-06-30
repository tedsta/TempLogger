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

socket.on('degree_days', on_degree_days);

function on_degree_days(deg_days) {
    $('#degree-days').text(deg_days);
}

// DOM manipulation
$(function () {
    $('#submit-datetime').submit(function (ev) {
        socket.emit('start_end_datetime', $('#start-datetime').val(), $('#end-datetime').val());
        return false;
    });
});
