# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver

from monitor.models import Message, Treatment
from monitor import apps as monitor
from monitor import tasks

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
        tasks.post_update.apply_async(args=[msg])

@receiver(post_save, sender=Message)
def save_message(sender, instance, created=False, **kwargs):
    if created:
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

        if message.msg_type == 'R' and len(treatment.messages.all()) == 1:
            diff = datetime.datetime.now() - message.created_at
            if diff <= datetime.timedelta(minutes=30):
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
                    last_rejected = treatment.person.treatments.filter(is_rejected=True, is_closed=True, closed_at__isnull=False).order_by('-closed_at').first()
                    if last_rejected is None or datetime.datetime.now() - last_rejected.closed_at >= datetime.timedelta(minutes=30):
                        message = Message()
                        message._dirty = True
                        message.treatment = treatment
                        message.created_at = datetime.datetime.now()
                        message.text = config.PLEASE_TREATMENT_INACTIVE_MESSAGE % web.utils.get_now_as_str()
                        message.msg_type = 'S'
                        message.save()

                        to_addr = config.EMAIL_ALERT_TO
                        subject = config.EMAIL_ALERT_SUBJECT
                        body = config.EMAIL_ALERT_BODY
                        body = body.replace('{{TREATMENT}}', treatment.pk)

                        tasks.send_email.apply_async(args=[to_addr, subject, body])

                    treatment.is_closed = True
                    treatment.is_rejected = True
                    treatment.closed_at = datetime.datetime.now()
                    treatment.save()

@receiver(post_save, sender=Treatment)
def save_treatment(sender, instance, created=False, **kwargs):
    if hasattr(instance, '_dirty'):
        return

    treatment = instance

    if treatment.is_closed:
        json_obj = {"action": "closed"}
        treatment.websocket_group.send({"text": json.dumps(json_obj)})
