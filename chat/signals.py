# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver

from monitor.models import Message, Treatment
from monitor import apps as monitor
from chat import consumers

import web.utils

@receiver(post_save, sender=Message)
def save_message(sender, instance=None, created=False, **kwargs):
    if created and instance is not None:
        message = instance
        treatment = message.treatment

        json_obj = {"action": "text", "message": message.text, "datetime": web.utils.get_datetime_as_str(message.created_at), "was_received": message.msg_type=='R'}
        treatment.websocket_group.send({"text": json.dumps(json_obj)})

        last_message = treatment.messages.filter(msg_type='R', is_sync=True).order_by('-created_at').first()

        if treatment.slots_date != last_message.created_at:
            treatment.slots_date = last_message.created_at
            treatment.slots_count = 5
            treatment.save()

@receiver(post_save, sender=Treatment)
def save_treatment(sender, instance=None, created=False, **kwargs):
    if instance is not None:
        treatment = instance

        if treatment.is_closed:
            json_obj = {"action": "closed"}
            treatment.websocket_group.send({"text": json.dumps(json_obj)})
        elif created:
            consumers.treatment_go(treatment)

def retry_send(message):
    with transaction.atomic():
        if not message.is_sync:
            treatment = message.treatment

            try:
                twitter_msg = monitor.twitter_api.PostDirectMessage(message.text, user_id=treatment.person.user_id)
                message.is_sync = True
                message.external_id = twitter_msg.id
                message.save()
                print("Mensagem local enviada: " + str(message.external_id))
            except Exception as e:
                print(e)
