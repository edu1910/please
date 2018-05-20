# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from constance import config

import twitter

twitter_api = None

class MonitorConfig(AppConfig):
    name = 'monitor'
    twitter_api = None

    def ready(self):
        global twitter_api
        print("Conectando ao Twitter...")
        twitter_api = twitter.Api(consumer_key=config.TWITTER_CONSUMER_KEY,
                consumer_secret=config.TWITTER_CONSUMER_SECRET,
                access_token_key=config.TWITTER_ACCESS_TOKEN_KEY,
                access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
                sleep_on_rate_limit=False)
        print("Conectado!")
