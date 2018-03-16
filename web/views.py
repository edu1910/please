from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.template.context_processors import csrf
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import datetime, re, json, pytz

from monitor.models import Person, Issue, Track, TweetBlackList, GroupManager
from monitor.controller import list_permissions

from web.permissions import admin_required, manager_required

def render(request, context, template):
    template = loader.get_template('web/' + template)

    context.update(list_permissions(request.user))

    return HttpResponse(template.render(context, request))

def handler500(request):
    response = render(request, {}, '500.html')
    response.status_code = 500
    return response

def handler404(request):
    response = render(request, {}, '404.html')
    response.status_code = 404
    return response

def user_login(request):
    if request.user.is_authenticated():
        return redirect('/')
    else:
        context = {'error': False}
        if (request.POST.has_key('username')
                and request.POST.has_key('password')):
            username = request.POST['username']
            password = request.POST['password']
            remember = request.POST.has_key('remember')

            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)

                if not remember:
                    request.session.set_expiry(0)

                return redirect('/')
            else:
                context['error'] = True

        context.update(csrf(request))

        template = loader.get_template('web/login.html')
        return HttpResponse(template.render(context, request))

@login_required
def user_logout(request):
    auth_logout(request)
    return redirect('/')

def goto_dashboard(request, context):
    context['page'] = 'dashboard'
    context['person_count'] = Person.objects.count()
    context['issue_count'] = Issue.objects.count()
    context['treatment_count'] = 0
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'dashboard.html')

@login_required
def page_perfil(request):
    context = {}
    context['page'] = 'perfil'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'perfil.html')

@login_required
def page_dashboard(request):
    return goto_dashboard(request, {})

@login_required
@permission_required("monitor.validate_issue")
def page_issues(request):
    context = {}
    context['page'] = 'issues'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'issues.html')

@login_required
@permission_required("monitor.offer_treatment")
def page_treatments(request):
    context = {}
    context['page'] = 'treatments'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'treatments.html')

@login_required
@admin_required()
def page_admin_groups(request):
    context = {}
    context['page'] = 'admin/groups'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'admin/groups.html')

@login_required
@manager_required()
def page_manager_users(request):
    context = {}
    context['page'] = 'manager/users'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'manager/users.html')

@login_required
@manager_required()
def page_manager_statistics(request):
    context = {}
    context['page'] = 'manager/statistics'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'manager/statistics.html')

@login_required
@admin_required()
def page_admin_settings(request):
    context = {}
    context['page'] = 'admin/settings'
    _update_context_with_user_info(request.user, context)

    return render(request, context, 'admin/settings.html')

#######################################
def _update_context_with_user_info(user, context):
    context['is_manager'] = user.is_superuser

    if not context['is_manager']:
        context['is_manager'] = GroupManager.objects.filter(user=user).count() > 0

    context['is_admin'] = user.is_superuser
