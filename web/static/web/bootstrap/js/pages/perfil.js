var validator_user;
var validator_pass;

$(function () {
    validator_user = $('#form_user').validate({
        rules: {
            name: "required",
        },
        highlight: function (input) {
            $(input).parents('.form-line').addClass('error');
        },
        unhighlight: function (input) {
            $(input).parents('.form-line').removeClass('error');
        },
        errorPlacement: function (error, element) {
            $(element).parents('.form-group').append(error);
        }
    });

    validator_pass = $('#form_pass').validate({
        rules: {
            name: "required",
        },
        highlight: function (input) {
            $(input).parents('.form-line').addClass('error');
        },
        unhighlight: function (input) {
            $(input).parents('.form-line').removeClass('error');
        },
        errorPlacement: function (error, element) {
            $(element).parents('.form-group').append(error);
        }
    });
});

function form_user_save() {
    if (validator_user.form()) {
        show_loading();

        name = $('#user_name').val()
        email = $('#user_email').val()

        var obj = { json_data: JSON.stringify({
            name: name,
            username: $('#user_username').val(),
            email: $('#user_email').val()
        })};

        url = '/api/user/perfil/'
        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'json',
            data: obj,
            success: function (data) {
                if (data.success) {
                    $('#name').html(name)
                    $('#email').html(email)
                    show_success("Dados alterados!");
                } else {
                    show_error(data.error_msg);
                }
            }
        }).error(function() {
            show_error('Erro no servidor.');
        }).always(function() {
            hide_loading();
        });
    }
}

function form_pass_save() {
    if (validator_pass.form()) {
        show_loading();

        var obj = { json_data: JSON.stringify({
            current_pass: $('#user_current_pass').val(),
            new_pass: $('#user_new_pass').val(),
            confirm_pass: $('#user_confirm_new_pass').val(),
        }) };

        url = '/api/user/pass/'
        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'json',
            data: obj,
            success: function (data) {
                if (data.success) {
                    show_success("Senha alterada!");
                    setTimeout( function(){
                        window.location.replace("/");
                    }, 2000);
                } else {
                    show_error(data.error_msg);
                }
            }
        }).error(function() {
            show_error('Erro no servidor.');
        }).always(function() {
            hide_loading();
        });
    }
}

function show_success(msg) {
    $.notify({
        message: msg
    },{
        type: 'success',
        z_index: 1050,
        placement: {
            align: 'center'
        }
    });
}

function show_error(msg) {
    $.notify({
        message: msg
    },{
        type: 'danger',
        z_index: 1050,
        placement: {
            align: 'center'
        }
    });
}

function show_loading() {
    $('.page-loader-wrapper').show();
}

function hide_loading() {
    $('.page-loader-wrapper').fadeOut();
}
