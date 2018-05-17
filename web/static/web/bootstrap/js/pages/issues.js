var issues = [];
var refreshIssues;

$('#table_issues').bootstrapTable({
    formatNoMatches: function () {
        return 'Opa! N&atilde;o temos nenhum Ponto de Aten&ccedil;&atilde;o aguardando triagem';
    }
});

$(function () {
    $('#table_issues').on('click-row.bs.table', function (e, row, $element) {
        var id = row['id'];

        for (var i = 0; i < issues.length; i++) {
            if (issues[i].id == id) {
                issues[i].confirmed = !issues[i].confirmed;

                $element.css('backgroundColor', issues[i].confirmed ? '#673AB7' : '');
                $element.css('color', issues[i].confirmed ? 'white' : '');
                break;
            }
        }
    });
});

function start_issues() {
    show_loading();

    var obj = {
        json_data: JSON.stringify({issues: issues, next: true})
    };

    if (refreshIssues) {
        refreshIssues.abort();
    }

    refreshIssues = $.ajax({
        url: '/api/issues/',
        type: 'POST',
        dataType: 'json',
        data: obj,
        success: function (data) {
            $('#start_card').hide();
            $('#issues_card').show();
            $('#table_issues').bootstrapTable("load", data['issues']);

            issues = []
            for (var i = 0; i < data['issues'].length; i++) {
                issue = {id: data['issues'][i].id, confirmed: false};
                issues.push(issue);
            }
        }
    }).always(function() {
        hide_loading();
    });
}

function continue_issues() {
    start_issues();
}

function stop_issues() {
    var obj = {
        json_data: JSON.stringify({issues: issues, next: false})
    };

    if (refreshIssues) {
        refreshIssues.abort();
    }

    refreshIssues = $.ajax({
        url: '/api/issues/',
        type: 'POST',
        dataType: 'json',
        data: obj,
        success: function (data) {
            $('#start_card').show();
            $('#issues_card').hide();

            issues = []
        }
    }).always(function() {
        hide_loading();
    });
}

function show_loading() {
    $('.page-loader-wrapper').show();
}

function hide_loading() {
    $('.page-loader-wrapper').fadeOut();
}


function unload_page() {
    //return "You have unsaved changes on this page. Do you want to leave this page and discard your changes or stay on this page?";
}

window.onbeforeunload = unload_page;
