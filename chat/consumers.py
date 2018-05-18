# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import web.utils

from django.core.cache import cache

from datetime import datetime

from channels.auth import channel_session_user_from_http, channel_session_user
from channels import Channel, Group as ChannelGroup

from monitor.models import Treatment, Message

from chat.utils import get_treatment_or_error, catch_client_error
from monitor.permissions import manager_required, has_permission_to_user

from chat.exceptions import ClientError

LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes


@channel_session_user_from_http
def ws_connect(message):
    message.channel_session['treatments'] = []
    message.reply_channel.send({"accept": True})

@channel_session_user
def ws_disconnect(message):
    ChannelGroup("treatment-waiting").discard(message.reply_channel)

    for treatment_id in message.channel_session.get("treatments", []):
        try:
            treatment = Treatment.objects.get(id=treatment_id)
            treatment.websocket_group.discard(message.reply_channel)
        except Treatment.DoesNotExist:
            pass

@channel_session_user
def ws_receive(message):
    payload = json.loads(message['text'].replace('\n', '\\n'))
    payload['reply_channel'] = message.content['reply_channel']
    Channel("treatment.receive").send(payload)

@channel_session_user
def treatment_wait(message):
    ChannelGroup("treatment-waiting").discard(message.reply_channel)
    ChannelGroup("treatment-waiting").add(message.reply_channel)

    message.reply_channel.send({"text": json.dumps({"action": "waiting"})})

    waiting_treatments = Treatment.objects.filter(user__isnull=True, is_closed=False).order_by('created_at', 'id')
    if len(waiting_treatments) > 0:
        _treatment_begin(message, waiting_treatments[0])
    else:
        try:
            current_treatment = Treatment.objects.get(user=message.user, is_closed=False)
            _treatment_begin(message, current_treatment)
        except:
            pass

@channel_session_user
def treatment_begin(message):
    treatment = get_treatment_or_error(message["treatment"], message.user)
    _treatment_begin(message, treatment)

@channel_session_user
def treatment_end(message):
    if int(message['treatment']) not in message.channel_session['treatments']:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    treatment = get_treatment_or_error(message["treatment"], message.user)
    _treatment_end(message, treatment)

@channel_session_user
@manager_required()
def treatment_follow(message):
    treatment = get_treatment_or_error(message["treatment"], message.user)
    _treatment_follow(message, treatment)

@channel_session_user
@manager_required()
def treatment_unfollow(message):
    if int(message['treatment']) not in message.channel_session['treatments']:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    treatment = get_treatment_or_error(message["treatment"], message.user)
    _treatment_unfollow(message, treatment)

@channel_session_user
def treatment_send(message):
    if int(message['treatment']) not in message.channel_session['treatments']:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    treatment = get_treatment_or_error(message["treatment"], message.user)
    _treatment_send(message, treatment)

def treatment_go(treatment):
    ChannelGroup("treatment-waiting").send({"text": json.dumps({"action": "go_treating", "treatment": treatment.id})})

def _treatment_begin(message, treatment):
    lock_id = "consumers.treatment-begin"

    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            if treatment is not None and (treatment.is_closed or (treatment.user is not None and treatment.user != message.user)):
                raise ClientError("TREATMENT_ACCESS_DENIED")


            try:
                current_treatment = Treatment.objects.get(user=message.user,is_closed=False)
            except:
                current_treatment = None

            if current_treatment:
                treatment = current_treatment
            else:
                treatment.user = message.user
                treatment.treatment_at = datetime.now()
                treatment.save()

            treatment.websocket_group.add(message.reply_channel)

            message.channel_session['treatments'] = list(set(message.channel_session['treatments']).union([treatment.id]))
            message.reply_channel.send({"text": json.dumps({"action": "treating", "treatment": treatment.id})})

            _send_treatment_messages(message.reply_channel, treatment)
        finally:
            release_lock()

def _send_treatment_messages(reply_channel, treatment):
    for treatment_message in treatment.messages.all().order_by('created_at', 'id'):
        json_ojb = {"action": "text", "message": treatment_message.text, "datetime": web.utils.get_datetime_as_str(treatment_message.created_at), "was_received": treatment_message.msg_type=='R'}
        reply_channel.send({"text": json.dumps(json_ojb)})

def _treatment_end(message, treatment):
    if treatment.is_closed or treatment.user != message.user:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    treatment.is_closed = True
    treatment.save()

    treatment.websocket_group.send({"text": json.dumps({"action": "closed"})})
    message.channel_session['treatments'] = list(set(message.channel_session['treatments']).difference([treatment.id]))

def _treatment_follow(message, treatment):
    if treatment.is_closed or treatment.user is None:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    if not has_permission_to_user(message.user, treatment.user.id):
        raise ClientError("TREATMENT_ACCESS_DENIED")

    if treatment.id not in message.channel_session['treatments']:
        treatment.websocket_group.add(message.reply_channel)
        message.channel_session['treatments'].append(treatment.id)

    message.reply_channel.send({"text": json.dumps({"action": "following", "volunteer": treatment.user.first_name})})
    _send_treatment_messages(message.reply_channel, treatment)

def _treatment_unfollow(message, treatment):
    treatment.websocket_group.discard(message.reply_channel)
    message.channel_session['treatments'].remove(treatment.id)

    message.reply_channel.send({"text": json.dumps({"action": "closed"})})

def _treatment_send(message, treatment):
    if message.user != treatment.user:
        raise ClientError("TREATMENT_ACCESS_DENIED")

    new_message = Message()
    new_message.treatment = treatment
    new_message.created_at = datetime.now()
    new_message.text = str(message["message"])
    new_message.msg_type = 'S'
    new_message.save()
