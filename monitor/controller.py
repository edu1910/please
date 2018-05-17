# -*- coding: utf-8 -*-
from __future__ import unicode_literals

def list_permissions(user):
    permissions = {}

    permissions['can_validate_issues'] = user.has_perm('monitor.validate_issue')
    permissions['can_offer_treatments'] = user.has_perm('monitor.offer_treatment')

    return permissions
