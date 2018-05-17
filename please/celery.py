# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from celery import Celery

from monitor import tasks

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'please.settings')

app = Celery('please')

app.conf.broker_url = 'redis://localhost:6379/0'
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(61.0, tasks.send_invites.s(), name='send_invites every 61 seconds')
    sender.add_periodic_task(61.0, tasks.receive_directs.s(), name='receive_directs every 61 seconds')
    sender.add_periodic_task(5.0,  tasks.send_directs.s(), name='send_directs every 5 seconds')
