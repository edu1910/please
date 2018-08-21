(function($) {
  "use strict"; // Start of use strict

  // Smooth scrolling using jQuery easing
  $('a.js-scroll-trigger[href*="#"]:not([href="#"])').click(function() {
    if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
      if (target.length) {
        $('html, body').animate({
          scrollTop: (target.offset().top - 48)
        }, 1000, "easeInOutExpo");
        return false;
      }
    }
  });

  // Closes responsive menu when a scroll trigger link is clicked
  $('.js-scroll-trigger').click(function() {
    $('.navbar-collapse').collapse('hide');
  });

  // Activate scrollspy to add active class to navbar items on scroll
  $('body').scrollspy({
    target: '#mainNav',
    offset: 54
  });

  // Collapse Navbar
  var navbarCollapse = function() {
    if ($("#mainNav").offset().top > 100) {
      $("#mainNav").addClass("navbar-shrink");
    } else {
      $("#mainNav").removeClass("navbar-shrink");
    }
  };
  // Collapse now if page is not at top
  navbarCollapse();
  // Collapse the navbar when page is scrolled
  $(window).scroll(navbarCollapse);

})(jQuery); // End of use strict


function submit_application() {
    isLegalAge = $("#checkLegalAge")[0].checked;
    name = $("#inputName")[0].value.trim();
    email = $("#inputEmail")[0].value.trim();
    isFemale = $("#radioFemale")[0].checked;
    isMale = $("#radioMale")[0].checked;

    $("#alerts").empty();

    if (!isFemale && !isMale) {
        show_alert("warning", "Por favor, informe como devemos te chamar.", 10000);
        return;
    }

    if (name.length == 0) {
        show_alert("warning", "Por favor, informe seu nome.", 10000);
        return;
    }

    if (!validateName(name)) {
        show_alert("warning", "Por favor, informe um nome v&aacute;lido.", 10000);
        return;
    }

    if (email.length == 0) {
        show_alert("warning", "Por favor, informe seu e-mail.", 10000);
        return;
    }

    if (!validateEmail(email)) {
        show_alert("warning", "Por favor, informe um e-mail v&aacute;lido.", 10000);
        return;
    }

    if (!isLegalAge) {
        show_alert("warning", "Desculpe, voc&ecirc; deve possuir ao menos 18 anos de idade para inscrever-se.", 10000);
        return;
    }

    data = {json_data: JSON.stringify({male:isMale, female:isFemale, name:name, email:email, legalAge:isLegalAge})};
    $('#volunteer_submit').addClass('disabled');
    $('#volunteer_submit').html('Aguarde...');
    $("#radioFemale").prop('disabled', true);
    $("#radioMale").prop('disabled', true);
    $("#checkLegalAge").prop('disabled', true);
    $("#inputName").prop('disabled', true);
    $("#inputEmail").prop('disabled', true);

    $.post(url="https://please.redeplis.org/api/volunteer/new/", data=data)
    .done(function(data) {
        console.log("data: " + data)
        if (data.success) {
            $("#radioFemale")[0].checked = false;
            $("#radioMale")[0].checked = false;
            $("#checkLegalAge")[0].checked = false;
            $("#inputName")[0].value = '';
            $("#inputEmail")[0].value = '';

            show_alert("success", "Legal! Confira em sua caixa de e-mail a mensagem que enviamos e confirme sua inscri&ccedil;&atilde;o.", 0);
        } else {
            show_alert("danger", "Ops! Estamos com algum problema em nossos servidores. Por favor, envie um e-mail para <a href=\"mailto:contato@redeplis.org\">contato@redeplis.org</a> com as informa&ccedil;&otilde;es da sua inscri&ccedil;&atilde;o.", 0);
        }
    })
    .fail(function() {
        show_alert("danger", "Ops! Estamos com algum problema em nossos servidores. Por favor, envie um e-mail para <a href=\"mailto:contato@redeplis.org\">contato@redeplis.org</a> com as informa&ccedil;&otilde;es da sua inscri&ccedil;&atilde;o.", 0);
    })
    .always(function() {
        $('#volunteer_submit').removeClass('disabled');
        $('#volunteer_submit').html('Enviar inscri&ccedil;&atilde;o');
        $("#radioFemale").prop('disabled', false);
        $("#radioMale").prop('disabled', false);
        $("#checkLegalAge").prop('disabled', false);
        $("#inputName").prop('disabled', false);
        $("#inputEmail").prop('disabled', false);
    });
}

function validateEmail(email) {
    var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function validateName(name) {
    var re = /^[a-zA-Z ]{2,50}$/;
    return re.test(String(name));
}

var alert_timeout = null;

function show_alert(type, message, timeout) {
    alert =
    "<div id=\"" + type + "_alert\" style=\"margin-top: 16px\" class=\"alert alert-" + type + " alert-dismissible fade show\" role=\"alert\">" +
    "  "+ message +
    "  <button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-label=\"Fechar\">" +
    "    <span aria-hidden=\"true\">&times;</span>" +
    "  </button>" +
    "</div>";

    $("#alerts").html(alert);

    clearTimeout(alert_timeout);

    if (timeout > 0) {
        alert_timeout = setTimeout(function() {
            $("#" + type + "_alert").alert('close');
        }, timeout);
    }
}
