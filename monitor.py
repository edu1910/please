#!/usr/bin/python
# -*- coding: latin-1 -*-
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "please.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.utils import timezone
from django.db import transaction

from monitor.models import Person, Issue, Track, TweetBlackList
from datetime import datetime

import config, signal, sys, twitter

has_exit = False

def signal_handler(signal, frame):
    global has_exit

    has_exit = True
    print('Bye')
    sys.exit(0)

def print_issue(issue):
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

    track_objects = Track.objects.all()
    tracks = []

    for track_object in track_objects:
        tracks.append(track_object.phrase)

    while not has_exit:
        stream = api.GetStreamFilter(track=tracks,languages=['pt'])
        print("Canal aberto!")

        try:
            while True:
                tweet = stream.next()

                user_id = tweet['user']['id']
                profile_image_url = tweet['user']['profile_image_url']
                location = tweet['user']['location']
                friends_count = tweet['user']['friends_count']
                name = tweet['user']['name']
                screen_name = tweet['user']['screen_name']
                status = 'I'

                tweet_id = tweet['id']
                tweet_url = None

                try:
                    tweet_url = tweet['entities']['urls'][0]['expanded_url']
                except:
                    pass

                text = tweet['text']
                coordinates = None
                created_at = None

                if tweet['is_quote_status']:
                    text = text + ': ' + tweet['quoted_status']['text']

                if not TweetBlackList.objects.filter(text=text, deny_count__gte=5):
                    with transaction.atomic():
                        try:
                            created_at = tweet['created_at'].replace('+0000 ', '')
                            created_at = timezone.datetime.strptime(created_at, '%a %b %d %H:%M:%S %Y')
                        except Exception as e:
                            print(e)
                            created_at = None

                        try:
                            person = Person.objects.get(user_id=user_id)
                        except:
                            person = Person()
                            person.user_id = user_id
                            person.status = status

                        person.profile_image_url = profile_image_url
                        person.location = location
                        person.friends_count = friends_count
                        person.name = name
                        person.screen_name = screen_name

                        person.save()

                        issue = Issue()

                        issue.person = person
                        issue.tweet_id = tweet_id
                        issue.tweet_url = tweet_url
                        issue.text = text
                        issue.coordinates = coordinates
                        issue.created_at = created_at
                        issue.status = 'I'

                        issue.save()

                        print_issue(issue)
                else:
                    print 'Blacklist: ' + text
        except Exception as e:
            print(e)

            try:
                stream.close()
            except Exception as e:
                print(e)
        finally:
            try:
                stream.close()
            except Exception as e:
                print(e)

if __name__ == "__main__":
    main()
