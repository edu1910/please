var refreshIssues;

$('#table_issues').bootstrapTable({
    formatNoMatches: function () {
        return 'Opa! N&atilde;o temos nenhum Ponto de Aten&ccedil;&atilde;o detectado';
    }
});

$(function () {
    $('.count-to').countTo();

    update_issues();

    setInterval(function() {
        update_issues();
    }, 10000);
});

function update_issues() {
    if (refreshIssues) {
        refreshIssues.abort()
    }

    refreshIssues = $.getJSON( "/api/dashboard/", function(data) {
        last_issue_count = parseInt($('#issue_count').html())
        last_person_count = parseInt($('#person_count').html())
        last_treatment_count = parseInt($('#treatment_count').html())

        $('#issue_count').countTo({from: last_issue_count, to: data.issue_count});
        $('#person_count').countTo({from: last_person_count, to: data.person_count});
        $('#treatment_count').countTo({from: last_treatment_count, to: data.treatment_count});

        $('#table_issues').bootstrapTable("load", data.issues);
    });
}
