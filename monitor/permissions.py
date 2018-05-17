# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import user_passes_test

from monitor.models import GroupManager

def admin_required(*args):
    def test_func(user):
        return user.is_superuser

    return user_passes_test(test_func)

def manager_required(*args):
    return user_passes_test(is_manager)

def is_manager(user):
    is_manager = user.is_superuser

    if not is_manager:
        is_manager = GroupManager.objects.filter(user=user).count() > 0

    return is_manager

def has_permission_to_group(req_user, group_id):
    has = req_user.is_superuser or (group_id is None and is_manager(req_user))

    if not has:
        try:
            group = Group.objects.get(id=group_id)
            groupManager = GroupManager.objects.get(group=group)
        except:
            groupManager = None

        has = (groupManager is not None) and (groupManager.user.id == req_user.id)

    return has

def has_permission_to_user(req_user, user_id):
    has = req_user.is_superuser or (user_id is None and is_manager(req_user))

    if not has:
        try:
            user = User.objects.get(id=user_id)
            groups = user.groups.all().order_by('name')
            has = len(groups) == 0

            if not has:
                for group in groups:
                    try:
                        groupManager = GroupManager.objects.get(group=group)
                        if groupManager.user.id == req_user.id:
                            has = True
                            break
                    except:
                        pass
        except:
            pass

    return has
