# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.cache import cache

from celery.task import Task
from celery import Celery
from celery import shared_task
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from datetime import datetime

logger = get_task_logger(__name__)
logger.setLevel(10)

LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes


@shared_task
def send_invites():
    from monitor import apps as monitor
    from monitor import models

    logger.debug("Enviando convites...")
    pending_invites = models.Invite.objects.filter(is_sync=False).order_by('-created_at')

    for pending_invite in pending_invites:
        monitor.twitter_api.PostUpdates(status=settings.PLEASE_INVITE_MESSAGE, \
            in_reply_to_status_id=pending_invite.issue.tweet_id, auto_populate_reply_metadata=True)
        pending_invite.is_sync = True
        pending_invite.sync_at = datetime.now()
        pending_invite.save()
        logger.info("Convite enviado: " + str(pending_invite.id))
    logger.debug("...convites enviados ;)")

@shared_task
def receive_directs():
    from monitor import apps as monitor
    from monitor import models

    lock_id = "direct.receive-lock"

    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    logger.debug("Recebendo directs...")
    if acquire_lock():
        try:
            try:
                last_message = models.Message.objects.filter(msg_type='R', is_sync=True).order_by('-external_id').first()
                since_id = last_message.external_id
            except Exception as e:
                logger.error(e)
                since_id = None

            directs = monitor.twitter_api.GetDirectMessages(since_id=since_id)

            for direct in reversed(directs):
                logger.info("Mensagem recebida: " + str(direct.id))
                _save_message(direct, direct.sender, 'R')

            try:
                last_message = models.Message.objects.filter(msg_type='S', is_sync=True).order_by('-external_id').first()
                since_id = last_message.external_id
            except Exception as e:
                logger.error(e)
                since_id = None

            directs = monitor.twitter_api.GetSentDirectMessages(since_id=since_id)

            for direct in reversed(directs):
                logger.info("Mensagem enviada: " + str(direct.id))
                _save_message(direct, direct.recipient, 'S')
        finally:
            release_lock()
        logger.debug("...directs recebidos ;)")
        return

    logger.debug("...directs estão sendo recebidos por outra tarefa")
    return

@shared_task
def new_receive_directs():
    from monitor import apps as monitor
    from monitor import models

    lock_id = "direct.receive-lock"

    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    logger.debug("Recebendo directs...")
    if acquire_lock():
        try:
            next_cursor, directs = monitor.twitter_api.DirectMessageEventList()

            for direct in reversed(directs):
                other_id = direct.sender_id
                direct_type = 'R'

                if settings.TWITTER_OWNER_ID == other_id:
                    other_id = direct.recipient_id
                    direct_type = 'S'

                _new_save_message(direct, other_id, direct_type)
        finally:
            release_lock()
        logger.debug("...directs recebidos ;)")
        return

    logger.debug("...directs estão sendo recebidos por outra tarefa")
    return

@shared_task
def send_directs():
    from monitor import apps as monitor
    from monitor import models

    lock_id = "direct.send-lock"

    acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    logger.debug("Enviando directs...")
    if acquire_lock():
        try:
            not_sent_messages = models.Message.objects.filter(is_sync=False)
            for not_sent_message in not_sent_messages:
                if not not_sent_message.is_sync:
                    treatment = not_sent_message.treatment

                    slots_date = None if treatment.slots_date is None else treatment.slots_date.date()

                    if slots_date == datetime.today().date() and treatment.slots_count > 0\
                            or slots_date != datetime.today().date() and treatment.slots_count >= 0:
                        try:
                            twitter_msg = monitor.twitter_api.DirectMessageEventNew(not_sent_message.text, user_id=treatment.person.user_id)
                            not_sent_message.is_sync = True
                            not_sent_message.external_id = twitter_msg.id
                            not_sent_message.save()

                            logger.debug("slots_count: " + str(treatment.slots_count))

                            if slots_date == datetime.today().date():
                                treatment.slots_count = treatment.slots_count-1
                            else:
                                treatment.slots_count = -1

                            treatment.save()

                            logger.debug("slots_count: " + str(treatment.slots_count))

                            logger.info("Enviando mensagem nova: " + str(not_sent_message.external_id))
                        except Exception as e:
                            logger.error(e)
        finally:
            release_lock()
        logger.debug("...directs enviados ;)")
        return

    logger.debug("...directs estão sendo enviados por outra tarefa")
    return

def _save_message(direct, user, msg_type):
    from monitor import models

    with transaction.atomic():
        try:
            person = models.Person.objects.get(user_id=user.id)
        except Exception as e:
            person = models.Person()
            person.user_id = user.id
            person.status = 'N'
            person.save()

        try:
            treatment = models.Treatment.objects.get(person=person, is_closed=False)
        except Exception as e:
            treatment = models.Treatment()
            treatment.person = person
            treatment.save()

        try:
            message = models.Message.objects.get(external_id=direct.id, msg_type=msg_type)
        except Exception as e:
            message = models.Message()
            message.external_id = direct.id
            message.msg_type = msg_type

        try:
            created_at = direct.created_at.replace('+0000 ', '')
            created_at = timezone.datetime.strptime(created_at, '%a %b %d %H:%M:%S %Y')
        except Exception as e:
            logger.error(e)
            created_at = None

        message.treatment = treatment
        message.created_at = created_at
        message.text = direct.text
        message.is_sync = True
        message.save()

def _new_save_message(direct, user_id, msg_type):
    from monitor import models

    with transaction.atomic():
        try:
            person = models.Person.objects.get(user_id=user_id)
        except Exception as e:
            person = models.Person()
            person.user_id = user.id
            person.status = 'N'
            person.save()

        try:
            treatment = models.Treatment.objects.get(person=person, is_closed=False)
        except Exception as e:
            treatment = models.Treatment()
            treatment.person = person
            treatment.save()

        try:
            message = models.Message.objects.get(external_id=direct.id, msg_type=msg_type)
        except Exception as e:
            message = models.Message()
            message.external_id = direct.id
            message.msg_type = msg_type
            logger.info("Recebendo mensagem nova: " + str(direct.id))

        if not message.is_sync:
            try:
                created_at = timezone.datetime.utcfromtimestamp(int(direct.created_timestamp)/1000)
            except Exception as e:
                logger.error(e)
                created_at = None

            message.treatment = treatment
            message.created_at = created_at
            message.text = direct.message_data.text
            message.is_sync = True
            message.save()