#!/usr/bin/python
# -*- coding: latin-1 -*-
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "please.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.utils import timezone
from django.db import transaction

from monitor.models import Person, Treatment, Message
from datetime import datetime

import config, signal, sys, time, twitter

has_exit = False

def signal_handler(signal, frame):
    global has_exit

    has_exit = True
    print('Bye')
    sys.exit(0)

def print_direct(direct):
    print '--------------------------------------'
    print 'Issue ' + ': ' + issue.text
    print 'Person' + ': @' + issue.person.name
    print '--------------------------------------'

def main():
    signal.signal(signal.SIGINT, signal_handler)
    print("Conectando...")

    api = twitter.Api(consumer_key=config.TWITTER_CONSUMER_KEY,
            consumer_secret=config.TWITTER_CONSUMER_SECRET,
            access_token_key=config.TWITTER_ACCESS_TOKEN_KEY,
            access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
            sleep_on_rate_limit=True)

    print("Conectado!")

    while not has_exit:
        try:
            while True:
                try:
                    last_message = Message.objects.filter(msg_type='R', is_sync=True).order_by('-external_id').first()
                    since_id = last_message.external_id
                except:
                    since_id = None

                directs = api.GetDirectMessages(since_id=since_id, full_text=True)

                for direct in directs:
                    print("Mensagem recebida: " + str(direct.id))
                    _save_message(direct, direct.sender, 'R')

                try:
                    last_message = Message.objects.filter(msg_type='S', is_sync=True).order_by('-external_id').first()
                    since_id = last_message.external_id
                except:
                    since_id = None

                directs = api.GetSentDirectMessages(since_id=since_id)

                for direct in directs:
                    print("Mensagem enviada: " + str(direct.id))
                    _save_message(direct, direct.recipient, 'S')

                time.sleep(5)
        except Exception as e:
            print(e)

def _save_message(direct, user, msg_type):
    with transaction.atomic():
        try:
            person = Person.objects.get(user_id=user.id)
        except:
            person = Person()
            person.user_id = user.id
            person.status = 'N'

        person.profile_image_url = user.profile_image_url
        person.location = user.location
        person.friends_count = user.friends_count
        person.name = user.name
        person.screen_name = user.screen_name

        person.save()

        try:
            treatment = Treatment.objects.get(person=person, is_closed=False)
        except Exception as e:
            treatment = Treatment()
            treatment.person = person
            treatment.save()

        try:
            message = Message.objects.get(external_id=direct.id, msg_type=msg_type)
        except:
            message = Message()
            message.external_id = direct.id
            message.msg_type = msg_type

        try:
            created_at = direct.created_at.replace('+0000 ', '')
            created_at = timezone.datetime.strptime(created_at, '%a %b %d %H:%M:%S %Y')
        except Exception as e:
            print(e)
            created_at = None

        message.treatment = treatment
        message.created_at = created_at
        message.text = direct.text
        message.is_sync = True
        message.save()

if __name__ == "__main__":
    main()
