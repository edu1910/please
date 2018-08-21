# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group, Permission
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.template.context_processors import csrf
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError

import datetime, re, json
import random
import web.utils

from monitor.models import Person, Issue, Track, TweetBlackList, GroupManager, Treatment, Message, Invite
from monitor.controller import list_permissions
from monitor.permissions import admin_required, manager_required, has_permission_to_group, has_permission_to_user
from monitor import tasks

from constance import config


@login_required
def dashboard(request):
    response_data = {}
    response_data['person_count'] = Person.objects.count()
    response_data['issue_count'] = Issue.objects.count()
    response_data['treatment_count'] = Treatment.objects.filter(is_closed=True).count()

    issues = Issue.objects.all().order_by('-created_at', '-id')[:20]

    response_data['issues'] = []

    for issue in issues:
        issue_json = {}
        issue_json['id'] = issue.id

        issue_json['created_at'] = web.utils.get_datetime_as_str(issue.created_at)
        issue_json['text'] = _encode_string_with_links(_normalize_text(issue.text)).replace("\n", "</br>")
        response_data['issues'].append(issue_json)

    return JsonResponse(response_data)

@login_required
@permission_required("monitor.validate_issue")
@csrf_exempt
@require_http_methods(["POST"])
def issues(request):
    first_call = True
    next_issues = True

    if 'json_data' in request.POST:
        request_json = json.loads(request.POST['json_data'])
        issues_json = request_json['issues']
        next_issues = bool(request_json['next'])
        first_call =  len(issues_json) == 0
        for issue_json in issues_json:
            try:
                issue = Issue.objects.get(id=int(issue_json['id']))
                issue.status = 'T' if bool(issue_json['confirmed']) else 'F'

                if issue_json['confirmed']:
                    issue.person.status = 'N'
                    issue.person.save()

                    invite_opened = Invite.objects.filter(is_sync=False, person=issue.person).first()

                    if invite_opened is None:
                        today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
                        today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)

                        today_invite = Invite.objects.filter(is_sync=True, sync_at__range=(today_min, today_max), person=issue.person).first()
                        if today_invite is None:
                            try:
                                invite = Invite()
                                invite.person = issue.person
                                invite.issue = issue
                                invite.save()
                            except:
                                pass
                    else:
                        invite_opened.created_at = datetime.datetime.now()
                        invite_opened.issue = issue
                        invite_opened.save()
                else:
                    try:
                        blacklist = TweetBlackList.objects.get(text=issue.text)
                        blacklist.deny_count = blacklist.deny_count+1
                        blacklist.save()
                    except:
                        blacklist = TweetBlackList()
                        blacklist.text = issue.text
                        blacklist.deny_count = 1
                        blacklist.save()

                issue.save()
            except:
                pass

    response_data = {}
    response_data['issues'] = []

    if next_issues:
        issues = Issue.objects.filter(status='I',validated_by__isnull=True).order_by('-created_at', '-id')[:10]

        for issue in issues:
            issue_json = {}
            issue_json['id'] = issue.id
            issue_json['created_at'] = web.utils.get_datetime_as_str(issue.created_at)
            issue_json['text'] = _encode_string_with_links(_normalize_text(issue.text)).replace("\n", "</br>")
            response_data['issues'].append(issue_json)

            issue.validated_by = request.user
            issue.validated_at = datetime.datetime.now()
            issue.save()

    return JsonResponse(response_data)

@login_required
@manager_required()
def manager_users(request):
    response_data = {}
    response_data['users'] = []

    users = User.objects.filter(is_active=True).order_by('first_name', 'username')

    for user in users:
        if has_permission_to_user(request.user, user.id):
            user_json = {}
            user_json['id'] = user.id
            user_json['name'] = user.first_name
            user_json['username'] = user.username
            user_json['email'] = user.email
            user_json['groups'] = _get_names_user_groups(user.groups.all().order_by('name'))

            response_data['users'].append(user_json)

    return JsonResponse(response_data)

@login_required
@csrf_exempt
@manager_required()
@require_http_methods(["GET", "POST", "DELETE"])
def manager_user(request, user_id=None):
    if request.method == "GET":
        return _admin_get_user(request, user_id)
    elif request.method == "POST":
        return _admin_edit_user(request, user_id)
    elif request.method == "DELETE":
        return _admin_delete_user(request, user_id)

@login_required
@manager_required()
def manager_treatments(request):
    response_data = {}
    response_data['treatments'] = []

    if request.user.is_superuser:
        treatments = Treatment.objects.filter(user__isnull=False, is_closed=False).order_by('created_at', 'id')
    else:
        groups = GroupManager.objects.filter(user=request.user).only('group')
        treatments = Treatment.objects.filter(user__isnull=False, is_closed=False, user__groups__in=groups).order_by('created_at', 'id')

    response_data['treatments'] = _treatments_to_json(treatments)

    return JsonResponse(response_data)

@login_required
@manager_required()
def admin_groups(request):
    response_data = {}
    response_data['groups'] = []

    groups = Group.objects.all().order_by('name')

    for group in groups:
        response_data['groups'].append(_group_to_json(request, group))

    return JsonResponse(response_data)

@login_required
@admin_required()
@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
def admin_group(request, group_id=None):
    if request.method == "GET":
        return _admin_get_group(request, group_id)
    elif request.method == "POST":
        return _admin_edit_group(request, group_id)
    elif request.method == "DELETE":
        return _admin_delete_group(request, group_id)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def user_perfil(request):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    if 'json_data' in request.POST:
        try:
            request_json = json.loads(request.POST['json_data'])

            name = request_json['name']
            username = request_json['username']
            email = request_json['email']

            user = request.user
            user.first_name = name
            user.username = username
            user.email = email
            user.save()

            response_data['success'] = True
        except IntegrityError as ie:
            response_data['error_msg'] = "J&aacute; existe um volunt&aacute;rio com este usu&aacute;rio."

    return JsonResponse(response_data)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def user_pass(request):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    if 'json_data' in request.POST:
        try:
            request_json = json.loads(request.POST['json_data'])

            current_pass = request_json['current_pass']
            new_pass = request_json['new_pass']
            confirm_pass = request_json['confirm_pass']

            user = request.user

            if not user.check_password(current_pass):
                response_data['error_msg'] = "Senha atual inv&aacute;lida."
            elif new_pass != confirm_pass:
                response_data['error_msg'] = "Confirma&ccedil;&atilde;o de senha n&atilde;o corresponde &agrave; digitada."
            else:
                user.set_password(new_pass)
                user.save()

                response_data['success'] = True
        except IntegrityError as ie:
            response_data['error_msg'] = "J&aacute; existe um volunt&aacute;rio com este nome."

    return JsonResponse(response_data)

@csrf_exempt
@require_http_methods(["POST"])
def volunteer_new(request):
    response_data = {'success': False}

    if 'json_data' in request.POST:
        request_json = json.loads(request.POST['json_data'])

        male = request_json['male']
        female = request_json['female']
        name = request_json['name']
        email = request_json['email']
        legalAge = request_json['legalAge']

        if legalAge:
            to_addr = email
            subject = config.EMAIL_NEW_VOLUNTEER_SUBJECT
            body = config.EMAIL_NEW_VOLUNTEER_BODY
            body = body.replace('{{NAME}}', name)
            body = body.replace('{{PRONOUN}}', 'Sr.' if male else 'Sra.')

            tasks.send_email.apply_async(args=[to_addr, subject, body])

            response_data['success'] = True

    return JsonResponse(response_data)

#######################################
def _admin_get_group(request, group_id):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    try:
        response_data['group'] = _group_to_data_json(request, Group.objects.get(id=group_id))
        response_data['success'] = True
    except:
        pass

    return JsonResponse(response_data)

def _admin_get_user(request, user_id):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    if has_permission_to_user(request.user, user_id):
        try:
            response_data['user'] = _user_to_data_json(request, User.objects.get(id=user_id))
            response_data['success'] = True
        except:
            pass

    return JsonResponse(response_data)

def _admin_delete_group(request, group_id=None):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    try:
        Group.objects.get(id=group_id).delete()
        response_data['success'] = True
    except:
        response_data['error_msg'] = "Grupo n&atilde;o cadastrado."

    return JsonResponse(response_data)

def _admin_delete_user(request, user_id=None):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    if has_permission_to_user(request.user, user_id):
        try:
            user = User.objects.get(id=user_id)
            cant = user.is_superuser or user.id == request.user.id

            if not cant:
                for group in user.groups.all():
                    if not has_permission_to_group(request.user, group.id):
                        cant = True
                        break

            if cant:
                response_data['error_msg'] = "Voc&ecirc; n&atilde;o pode excluir este usu&aacute;rio."
            else:
                user.is_active = False
                user.save()
                GroupManager.objects.filter(user=user).delete()
                response_data['success'] = True
        except:
            response_data['error_msg'] = "Volunt&aacute;rio n&atilde;o cadastrado."

    return JsonResponse(response_data)

def _admin_edit_group(request, group_id=None):
    return _admin_save_group(request, Group.objects.get(id=group_id) if group_id is not None else None)

def _admin_edit_user(request, user_id=None):
    return _admin_save_user(request, User.objects.get(id=user_id) if user_id is not None else None)

def _admin_save_group(request, group=None):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    if 'json_data' in request.POST:
        try:
            request_json = json.loads(request.POST['json_data'])

            name = request_json['name']
            manager = request_json['manager']
            can_treatment = request_json['can_treatment']
            can_validate = request_json['can_validate']

            with transaction.atomic():
                if group is None:
                    group = Group()
                group.name = name
                group.save()

                group.permissions.clear()

                if manager is None or len(manager) == 0:
                    GroupManager.objects.filter(group=group).delete()

                if can_treatment:
                    group.permissions.add(Permission.objects.get(codename="offer_treatment"))
                if can_validate:
                    group.permissions.add(Permission.objects.get(codename="validate_issue"))
                if manager is not None and len(manager) > 0:
                    groupManager = None

                    try:
                        groupManager = GroupManager.objects.get(group=group)
                    except:
                        groupManager = GroupManager()
                        groupManager.group = group

                    groupManager.user = User.objects.get(id=int(manager))
                    groupManager.save()

                group.save()
            response_data['success'] = True
        except IntegrityError as ie:
            response_data['error_msg'] = "J&aacute; existe um grupo com este nome."

    return JsonResponse(response_data)

def _admin_save_user(request, user=None):
    response_data = {'success': False}
    response_data['error_msg'] = "Erro no servidor."

    if has_permission_to_user(request.user, user.id if user is not None else None):
        if 'json_data' in request.POST:
            try:
                request_json = json.loads(request.POST['json_data'])

                name = request_json['name']
                username = request_json['username']
                email = request_json['email']
                groups = request_json['groups']
                reset_password = request_json['reset_password']

                with transaction.atomic():
                    if user is None:
                        user = User()
                    user.first_name = name
                    user.username = username
                    user.email = email
                    user.save()

                    if reset_password:
                        user.set_password(user.username)

                    if not groups:
                        groups = []

                    current_groups = user.groups.all()
                    for current_group in current_groups:
                        if current_group.id not in groups:
                            if has_permission_to_group(request.user, current_group.id):
                                user.groups.remove(current_group)

                    for group in groups:
                        if has_permission_to_group(request.user, group):
                            user.groups.add(Group.objects.get(id=group))

                    user.save()

                response_data['success'] = True
            except IntegrityError as ie:
                response_data['error_msg'] = "J&aacute; existe um volunt&aacute;rio com este usu&aacute;rio."

    return JsonResponse(response_data)

def _user_to_data_json(request, user):
    user_json = {}
    user_json['id'] = user.id
    user_json['name'] = user.first_name
    user_json['username'] = user.username
    user_json['email'] = user.email

    user_json['groups'] = []
    for group in user.groups.all().order_by('name'):
        user_json['groups'].append(_group_to_data_json(request, group))

    return user_json

def _group_to_data_json(request, group):
    group_json = {}
    group_json['id'] = group.id
    group_json['name'] = group.name
    group_json['has_permission'] = has_permission_to_group(request.user, group.id)

    manager = _get_group_manager(group)
    if manager != None:
        manager_name = None

        if manager.user.first_name:
            manager_name = manager.user.get_short_name()
        else:
            manager_name = manager.user.username

        group_json['manager'] = {'name':manager_name, 'id':manager.user.id}
    else:
        group_json['manager'] = None

    group_json['can_validate'] = _has_permission(group, 'validate_issue')
    group_json['can_treatment'] = _has_permission(group, 'offer_treatment')

    return group_json

def _treatments_to_json(treatments):
    treatments_json = []

    for treatment in treatments:
        treatment_json = {}
        treatment_json['id'] = treatment.id
        treatment_json['user'] = treatment.user.first_name
        treatments_json.append(treatment_json)

    return treatments_json

def _group_to_json(request, group):
    group_json = {}
    group_json['id'] = group.id
    group_json['name'] = group.name
    group_json['has_permission'] = has_permission_to_group(request.user, group.id)

    manager = _get_group_manager(group)
    manager_name = None
    if manager != None:
        if manager.user.first_name:
            manager_name = manager.user.get_short_name()
        else:
            manager_name = manager.user.username

    group_json['manager'] = manager_name
    group_json['can_validate'] = _has_permission_str(group, 'validate_issue')
    group_json['can_treatment'] = _has_permission_str(group, 'offer_treatment')

    return group_json

def _normalize_text(text):
    chars_count = 0
    normalized_text = ""

    for c in text:
        if c == ' ':
            chars_count = 0

        chars_count += 1
        normalized_text += c

        if chars_count > 30:
            normalized_text += ' '
            chars_count = 0

    return normalized_text

def _encode_string_with_links(unencoded_string):
    URL_REGEX = re.compile(r"((http://|https://)[^ <>'\"{}|\\^`^:[\]]*)")
    return URL_REGEX.sub(r'', unencoded_string)

def _get_group_manager(group):
    manager = None
    try:
        manager = GroupManager.objects.get(group=group)
    except:
        pass
    return manager

def _has_permission_str(group, perm):
    return "Sim" if _has_permission(group, perm) else "N&atilde;o"

def _has_permission(group, perm):
    can = False
    try:
        group.permissions.get(codename=perm)
        can = True
    except:
        pass

    return can

def _get_names_user_groups(groups):
    names = []

    for group in groups:
        names.append(group.name)

    return ", ".join(names) if len(names) > 0 else None
