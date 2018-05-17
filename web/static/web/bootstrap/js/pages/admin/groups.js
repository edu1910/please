var validator;
var edit_id = null;
var refreshGroups;
var refreshUsers;

$('#table_groups').bootstrapTable({
    formatNoMatches: function () {
        return 'Opa! N&atilde;o temos nenhum Grupo a exibir';
    }
});

$(function () {
    validator = $('#form_group').validate({
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

    update_groups();

    $('#table_groups').on('click-row.bs.table', function (e, row, $element) {
        var id = row['id'];
        edit_group(id);
    });

    $("#defaultModal").on("hidden.bs.modal", function () {
        update_groups();
        $('#group_name')[0].value = "";
        $('#group_can_validate').prop("checked", false)
        $('#group_can_treatment').prop("checked", false)

        validator.resetForm();
    });

    $("#defaultModal").on("show.bs.modal", function () {
        update_users();
    });
});

function update_groups() {
    show_loading();
    if (refreshGroups) {
        refreshGroups.abort();
    }
    refreshGroups = $.getJSON( "/api/admin/groups/", function(data) {
        $('#table_groups').bootstrapTable("load", data.groups);
    }).always(function() {
        hide_loading();
    });
}

function update_users() {
    show_loading();
    if (refreshUsers) {
        refreshUsers.abort();
    }
    refreshUsers = $.ajax({
        url: "/api/manager/users/",
        type: 'GET',
        async: false,
        success: function (data) {
            select = $("#group_manager");
            select.html('');
            users = data['users'];

            select.append($('<option>', {
                value: '',
                text: '-- Selecione quem coordena --'
            }));

            $.each(users, function(key, val) {
                select.append($('<option>', {
                    value: val['id'],
                    text: val['name'] + ' (' + val['username'] +')'
                }));
            });
            select.selectpicker('refresh');
        }
    }).always(function() {
        hide_loading();
    });
}

function new_group() {
    $('#defaultModal').modal('show');
    $('#btn_delete').hide();
    $('#defaultModalLabel').html("NOVO GRUPO");
    edit_id = null;
}

function edit_group(group_id) {
    edit_id = group_id;
    $('#defaultModal').modal('show');
    $('#btn_delete').show();
    $('#defaultModalLabel').html("EDITAR GRUPO");

    show_loading();
    $.getJSON( "/api/admin/group/" + group_id, function(data) {
        if (data.success) {
            $('#group_name').val(data.group.name)
            $('#group_can_validate').prop("checked", data.group.can_validate)
            $('#group_can_treatment').prop("checked", data.group.can_treatment)

            if (data.group.manager) {
                $('#group_manager').selectpicker('val', data.group.manager.id);
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

        url = '/api/admin/group/' + edit_id + '/'

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
            can_treatment: $('#group_can_treatment').prop("checked"),
            can_validate: $('#group_can_validate').prop("checked"),
            manager: $('#group_manager').val(),
            name: $('#group_name').val()
        }) };

        url = '/api/admin/group/' + (edit_id ? edit_id + '/' : '')
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
