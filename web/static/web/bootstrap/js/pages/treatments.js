var refreshTreatmentsId;
var refreshTreatments;
var chat_websocket;
var closeTimeoutId;
var treatment;

$(function () {
    resize_treatments_content();
    scroll_chat();

    $("#text_chat").keydown(function(e) {
        var code = e.keyCode ? e.keyCode : e.which;
        if (code == 13 && !e.shiftKey) {
            e.preventDefault();
            send_message();
       }
    });

    options_treatment();
});

function stop_treatments() {
    chat_websocket.send('{"command": "end", "treatment": '+ treatment +'}');
}

function get_websocket_url() {
    var loc = window.location, url;
    if (loc.protocol === "https:") {
        url = "wss:";
    } else {
        url = "ws:";
    }
    url += "//" + loc.host;

    return url;
}

function cancel_refresh_treatments() {
    clearInterval(refreshTreatmentsId);
    clearTimeout(closeTimeoutId);

    if (refreshTreatments) {
        refreshTreatments.abort();
    }
}

function update_opened_treatments() {
    cancel_refresh_treatments();

    refreshTreatments = $.getJSON( "/api/manager/treatments/", function(data) {
        treatments = data['treatments'];

        clear_treatments();

        if (treatments.length > 0) {
            $('#treatments_loading').hide();
            $('#treatments_body').show();
        } else {
            $('#treatments_loading').show();
            $('#treatments_body').hide();
        }

        $.each(treatments, function(key, val) {
            add_treatment(val['id'], val['user'], false);
        });
    });
}

function resize_treatments_content() {
    var width = 20;
    $('#treatments_content div').each(function() {
        width += $(this).outerWidth(true) ;
    });
    $('#treatments_content').css('width', width + "px");
}

function options_treatment() {
    cancel_refresh_treatments();

    $('#chat_volunteer_name').html("");
    $('#start_card').show();
    $('#chat_card').hide();
    $('#chat_closed').hide();
    $('#chat_loading').hide();
    $('#chat_panel').hide();
    $('#chat_footer').hide();

    if (is_manager) {
        $('#treatments_card').show();
        update_opened_treatments();

        refreshTreatmentsId = setInterval(function() {
            update_opened_treatments();
        }, 10000);
    }
}

function closed_treatment() {
    $('#chat_closed').show();
    closeTimeoutId = setTimeout(function() {
        if (chat_websocket) {
            chat_websocket.close();
        }

        options_treatment();
    }, 5000);
}

function waiting_treatment() {
    $('#chat_volunteer_name').html("");
    $('#start_card').hide();
    $('#treatments_card').hide();
    $('#chat_card').show();
    $('#chat_closed').hide();
    $('#chat_loading').show();
    $('#chat_panel').hide();
    $('#chat_footer').hide();
}

function doing_treatment(data) {
    $('#chat_volunteer_name').html("Volunt&aacute;rio: " + user_first_name);
    $('#start_card').hide();
    $('#treatments_card').hide();
    $('#chat_card').show();
    $('#chat_closed').hide();
    $('#chat_loading').hide();
    $('#chat_panel').show();
    $('#chat_footer').show();

    treatment = data['treatment'];
}

function waiting_following_treatment() {
    $('#chat_volunteer_name').html("");
    $('#start_card').show();
    $('#treatments_card').show();
    $('#chat_card').show();
    $('#chat_closed').hide();
    $('#chat_loading').show();
    $('#chat_panel').hide();
    $('#chat_footer').hide();
}

function following_treatment(data) {
    $('#chat_volunteer_name').html("Volunt&aacute;rio: " + data['volunteer']);
    $('#start_card').show();
    $('#treatments_card').show();
    $('#chat_card').show();
    $('#chat_closed').hide();
    $('#chat_loading').hide();
    $('#chat_panel').hide();
    $('#chat_footer').hide();
}

function text_treatment(data) {
    add_chat(data['message'], data['datetime'], data['was_received']);
}

function start_treatment() {
    cancel_refresh_treatments();
    clear_chat();

    waiting_treatment();

    if (chat_websocket) {
        chat_websocket.close();
    }

    chat_websocket = new WebSocket(get_websocket_url());
    chat_websocket.onopen = function() {
        chat_websocket.send('{"command": "wait"}');
    }

    chat_websocket.onclose = function() {
        options_treatment();
    }

    chat_websocket.onerror = function() {
        options_treatment();
    }

    chat_websocket.onmessage = function(message) {
        var data = JSON.parse(message.data);

        if (data['action'] == 'text') {
            text_treatment(data);
        } else if (data['action'] == 'closed') {
            closed_treatment();
        } else if (data['action'] == 'waiting') {
            waiting_treatment();
        } else if (data['action'] == 'treating') {
            doing_treatment(data);
        } else if (data['action'] == 'go_treating') {
            chat_websocket.send('{"command": "begin", "treatment": '+ data['treatment'] +'}');
        }
    }
}

function send_message() {
    if (chat_websocket) {
        text_chat = $('#text_chat');
        message = text_chat.val();

        if (message.replace(/(?:\r\n|\r|\n)/g, '').length > 0) {
            chat_websocket.send('{"command": "send", "treatment": '+ treatment +', "message": "' + message + '"}');
            text_chat.val('')
        }
    }
}

function follow_treatment(id) {
    cancel_refresh_treatments();
    clear_chat();

    waiting_following_treatment();

    if (chat_websocket) {
        chat_websocket.close();
    }

    chat_websocket = new WebSocket(get_websocket_url());
    chat_websocket.onopen = function() {
        chat_websocket.send('{"command": "follow", "treatment": '+id+'}');
    }

    chat_websocket.onclose = function() {
        options_treatment();
    }

    chat_websocket.onerror = function() {
        options_treatment();
    }

    chat_websocket.onmessage = function(message) {
        var data = JSON.parse(message.data);

        if (data['action'] == 'text') {
            text_treatment(data);
        } else if (data['action'] == 'closed') {
            closed_treatment();
        } else if (data['action'] == 'following') {
            following_treatment(data);
        }
    }
}

function clear_treatments() {
    var content = $('#treatments_content');
    content.empty();
}

function add_treatment(id, user, before) {
    var content = $('#treatments_content');
    var child = '<div class="btn waves-effect treatment-item" onclick="javascript:follow_treatment('+ id +');">' +
                    '<h4>' + id + '</h4>' +
                    '<small>' + user + '</small>' +
                '</div>';

    if (before) {
        content.prepend(child);
    } else {
        content.append(child);
    }
    resize_treatments_content();
}

function scroll_chat() {
    var content = $('#chat_content');
    //content.animate({ scrollTop: content.prop("scrollHeight")}, 1);
    content.prop("scrollTop", content.prop("scrollHeight"));
}

function add_chat(title, datetime, rcvd) {
    title = title.replace(/(?:\r\n|\r|\n)/g, '<br />');

    var url = title.match(/(((ftp|https?):\/\/)[\-\w@:%_\+.~#?,&\/\/=]+)|((mailto:)?[_.\w-]+@([\w][\w\-]+\.)+[a-zA-Z]{2,3})/g);
    $.each(url, function(i, v) {
        title = title.replace(v, "<b>[CONTEÚDO BLOQUEADO]</b>");
    });

    var content = $('#chat_content');
    var child = '<div class="chat-message chat-message-' + (rcvd ? 'rcvd' : 'sent') + '">' +
                    '<p class="title">' + title + '</p>' +
                    '<p class="datetime">' + datetime + '</p>' +
                '</div>';

    content.append(child);
    scroll_chat();
}

function clear_chat() {
    var content = $('#chat_content');
    content.empty();

    content = $('#text_chat');
    content.val('');
}

function show_loading() {
    $('.page-loader-wrapper').show();
}

function hide_loading() {
    $('.page-loader-wrapper').fadeOut();
}
