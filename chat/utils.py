# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from chat.exceptions import ClientError
from monitor.models import Treatment

def catch_client_error(func):
    @wraps(func)
    def inner(message, *args, **kwargs):
        try:
            return func(message, *args, **kwargs)
        except ClientError as e:
            e.send_to(message.reply_channel)
    return inner

def get_treatment_or_error(treatment_id, user):
    if not user.is_authenticated:
        raise ClientError("USER_HAS_TO_LOGIN")
    try:
        treatment = Treatment.objects.get(id=treatment_id)
    except Treatment.DoesNotExist:
        raise ClientError("TREATMENT_INVALID")

    has_perm = user.is_superuser or user.has_perm('monitor.offer_treatment')
    if not has_perm:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    return treatment
