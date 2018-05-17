#!/usr/bin/python
# -*- coding: latin-1 -*-
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "please.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.utils import timezone
from django.db import transaction

from monitor.models import Person, Treatment, Message
from monitor import apps as monitor

from datetime import datetime

import config, signal, sys, time, twitter

import chat.signals

has_exit = False

def signal_handler(signal, frame):
    global has_exit

    has_exit = True
    print('Bye')
    sys.exit(0)

def print_direct(direct):
    print('--------------------------------------')
    print('Issue ' + ': ' + issue.text)
    print('Person' + ': @' + issue.person.name)
    print('--------------------------------------')

def run():
    signal.signal(signal.SIGINT, signal_handler)

    while not has_exit:
        try:
            while True:
                print("Loooooop")
                try:
                    last_message = Message.objects.filter(msg_type='R', is_sync=True).order_by('-external_id').first()
                    since_id = last_message.external_id
                except Exception as e:
                    print(e)
                    since_id = None

                next_cursor, directs = monitor.twitter_api.DirectMessageEventList(count=1)

                for direct in directs:
                    print("Mensagem recebida: " + str(direct.id))
                    #_save_message(direct, direct.sender, 'R')

                next_cursor, directs = monitor.twitter_api.DirectMessageEventList(count=1, cursor=next_cursor)

                for direct in directs:
                    print("Mensagem recebida: " + str(direct.id))
                    #_save_message(direct, direct.sender, 'R')

                try:
                    last_message = Message.objects.filter(msg_type='S', is_sync=True).order_by('-external_id').first()
                    since_id = last_message.external_id
                except Exception as e:
                    print(e)
                    since_id = None

                '''directs = monitor.twitter_api.GetSentDirectMessages(since_id=since_id)

                for direct in directs:
                    print("Mensagem enviada: " + str(direct.id))
                    _save_message(direct, direct.recipient, 'S')'''

                not_sent_messages = Message.objects.filter(is_sync=False)
                for not_sent_message in not_sent_messages:
                    chat.signals.retry_send(not_sent_message)

                time.sleep(5)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    run()
