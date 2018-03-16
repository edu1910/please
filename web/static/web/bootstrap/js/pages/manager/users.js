var validator;
var edit_id = null;

$('#table_users').bootstrapTable({
    formatNoMatches: function () {
        return 'Opa! N&atilde;o temos nenhum <i>Volunt&aacute;rio</i> a exibir';
    }
});

$(function () {
    validator = $('#form_user').validate({
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

    if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent))) {
        $('#user_groups').multiSelect({ selectableOptgroup: false });
    }

    update_users();

    $('#table_users').on('click-row.bs.table', function (e, row, $element) {
        var id = row['id'];
        edit_user(id);
    });

    $("#defaultModal").on("hidden.bs.modal", function () {
        update_users();
        $('#user_name')[0].value = "";
        $('#user_username')[0].value = "";
        $('#user_email')[0].value = "";
        $('#reset_password').prop("checked", false);

        validator.resetForm();
    });

    $("#defaultModal").on("show.bs.modal", function () {
        update_groups();
    });
});

function update_users() {
    show_loading();
    $.getJSON( "/api/manager/users", function(data) {
        $('#table_users').bootstrapTable("load", data.users);
    }).always(function() {
        hide_loading();
    });
}

function update_groups() {
    show_loading();
    $.ajax({
        url: "/api/admin/groups",
        type: 'GET',
        async: false,
        success: function (data) {
            select = $("#user_groups");
            select.html('');
            groups = data['groups'];

            $.each(groups, function(key, val) {
                select.append($('<option>', {
                    value: val['id'],
                    text: val['name'],
                    selected: false,
                    disabled: !val['has_permission']
                }));
            });

            if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent))) {
                select.multiSelect('refresh');
            }
        }
    }).always(function() {
        hide_loading();
    });
}

function new_user() {
    $('#defaultModal').modal('show');
    $('#btn_delete').hide();
    $('#defaultModalLabel').html("NOVO VOLUNT&Aacute;RIO");
    $('#reset_password').prop("checked", true);
    $('#reset_password').prop("disabled", true);
    edit_id = null;
}

function edit_user(user_id) {
    edit_id = user_id;
    $('#defaultModal').modal('show');
    $('#btn_delete').show();
    $('#defaultModalLabel').html("EDITAR VOLUNT&Aacute;RIO");
    $('#reset_password').prop("checked", false);
    $('#reset_password').prop("disabled", false);

    show_loading();
    $.getJSON( "/api/manager/user/" + user_id, function(data) {
        if (data.success) {
            $('#user_name').val(data.user.name)
            $('#user_username').val(data.user.username)
            $('#user_email').val(data.user.email)

            select = []
            disabled = []
            data.user.groups.forEach(function(group) {
                select.push('' + group.id);

                if ($('option[value='+ group.id +']').prop('disabled')) {
                    disabled.push('' + group.id);
                    $('option[value='+ group.id +']').prop('disabled', false);
                }

                if ((/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent))) {
                    $('option[value='+ group.id +']').prop('selected', true);
                }
            })

            if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent))) {
                $("#user_groups").multiSelect('select', select);
            }

            disabled.forEach(function(group_id) {
                $('option[value='+ group_id +']').prop('disabled', true);
            })

            if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent))) {
                $("#user_groups").multiSelect('refresh');
            }
        } else {
            $('#defaultModal').modal('hide');
        }
    }).error(function() {
        $('#defaultModal').modal('hide');
    }).always(function() {
        hide_loading();
    });
}

function form_delete() {
    swal({
        title: "Você tem certeza?",
        text: "Você não será capaz de desfazer esta ação.",
        type: "warning",
        showCancelButton: true,
        confirmButtonColor: "#DD6B55",
        confirmButtonText: "EXCLUIR",
        cancelButtonText: "CANCELAR",
        closeOnConfirm: true
    }, function () {
        show_loading();

        url = '/api/manager/user/' + edit_id + '/'

        $.ajax({
            url: url,
            type: 'DELETE',
            success: function (data) {
                if (data.success) {
                    $('#defaultModal').modal('hide');
                } else {
                    show_error(data.error_msg);
                }
            }
        }).error(function() {
            show_error('Erro no servidor.');
        }).always(function() {
            hide_loading();
        });
    });
}

function form_save() {
    if (validator.form()) {
        show_loading();

        var obj = { json_data: JSON.stringify({
            name: $('#user_name').val(),
            username: $('#user_username').val(),
            email: $('#user_email').val(),
            groups: $("#user_groups").val(),
            reset_password: $('#reset_password').prop("checked")
        }) };

        url = '/api/manager/user/' + (edit_id ? edit_id + '/' : '')
        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'json',
            data: obj,
            success: function (data) {
                if (data.success) {
                    $('#defaultModal').modal('hide');
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
