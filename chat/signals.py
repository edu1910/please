# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver

from monitor.models import Message, Treatment
from monitor import apps as monitor

from chat import consumers

from constance import config
from constance.signals import config_updated

import web.utils
import datetime


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key == 'PLEASE_TREATMENT_IS_ACTIVE':
        if new_value:
            msg = config.PLEASE_TREATMENT_ACTIVE_TWEET_MESSAGE
        else:
            msg = config.PLEASE_TREATMENT_INACTIVE_TWEET_MESSAGE

        msg = msg % web.utils.get_now_as_str()

        monitor.twitter_api.PostUpdates(status=msg)

@receiver(post_save, sender=Message)
def save_message(sender, instance=None, created=False, **kwargs):
    if created and instance is not None:
        if hasattr(instance, '_dirty'):
            return

        message = instance
        treatment = message.treatment

        json_obj = {"action": "text", "message": message.text, "datetime": web.utils.get_datetime_as_str(message.created_at), "was_received": message.msg_type=='R'}
        treatment.websocket_group.send({"text": json.dumps(json_obj)})

        last_message = treatment.messages.filter(msg_type='R', is_sync=True).order_by('-created_at').first()

        if last_message is not None and treatment.slots_date != last_message.created_at:
            if not treatment.is_closed:
                treatment.slots_date = last_message.created_at
                treatment.slots_count = 5
                treatment.save()

@receiver(post_save, sender=Treatment)
def save_treatment(sender, instance=None, created=False, **kwargs):
    if instance is not None:
        if hasattr(instance, '_dirty'):
            return

        treatment = instance

        if created:
            if config.PLEASE_TREATMENT_IS_ACTIVE:
                if not consumers.treatment_go(treatment):
                    message = Message()
                    message._dirty = True
                    message.treatment = treatment
                    message.created_at = datetime.datetime.now()
                    message.text = config.PLEASE_TREATMENT_WAITING_MESSAGE % web.utils.get_now_as_str()
                    message.msg_type = 'S'
                    message.save()
            else:
                treatment._dirty = True
                treatment.is_closed = True
                treatment.save()
                message = Message()
                message._dirty = True
                message.treatment = treatment
                message.created_at = datetime.datetime.now()
                message.text = config.PLEASE_TREATMENT_INACTIVE_MESSAGE % web.utils.get_now_as_str()
                message.msg_type = 'S'
                message.save()
        elif treatment.is_closed:
            json_obj = {"action": "closed"}
            treatment.websocket_group.send({"text": json.dumps(json_obj)})

def retry_send(message):
    with transaction.atomic():
        if not message.is_sync:
            treatment = message.treatment

            try:
                twitter_msg = monitor.twitter_api.PostDirectMessage(message.text, user_id=treatment.person.user_id)
                message.is_sync = True
                message.external_id = twitter_msg.id
                message.save()
            except Exception as e:
                pass
