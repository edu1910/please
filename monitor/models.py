from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.six import python_2_unicode_compatible

from channels import Group as ChannelGroup

from simple_history.models import HistoricalRecords

import datetime


@python_2_unicode_compatible
class GroupManager(models.Model):
    history = HistoricalRecords()

    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
       return self.user.first_name

@python_2_unicode_compatible
class Profile(models.Model):
    history = HistoricalRecords()

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatar', blank=True, null=True)

    def __str__(self):
       return self.user.first_name

@python_2_unicode_compatible
class Person(models.Model):
    STATUS = (
        ('I', 'Identified'),
        ('N', 'Needs care'),
        ('D', 'Dispensed'),
    )

    history = HistoricalRecords()

    user_id = models.CharField(max_length=32)
    status = models.CharField(max_length=1, choices=STATUS)

    def __str__(self):
       return self.user_id

@python_2_unicode_compatible
class Issue(models.Model):
    STATUS = (
        ('I', 'Identified'),
        ('T', 'True'),
        ('F', 'False'),
    )

    history = HistoricalRecords()

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    tweet_id = models.CharField(max_length=32)
    tweet_url = models.CharField(max_length=256, blank=True, null=True)
    text = models.CharField(max_length=560)
    coordinates = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField()
    status = models.CharField(max_length=1, choices=STATUS)
    validated_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    validated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        s = self.person.__str__() + ': '
        if self.tweet_url is not None:
            s = s + self.tweet_url
        else:
            s = s + self.text
        return s

    class Meta:
        permissions = (
            ("validate_issue", "Can validate identified issues"),
        )

@python_2_unicode_compatible
class Track(models.Model):
    history = HistoricalRecords()

    phrase = models.CharField(max_length=32)

    def __str__(self):
       return self.phrase

@python_2_unicode_compatible
class TweetBlackList(models.Model):
    history = HistoricalRecords()

    text = models.CharField(max_length=560)
    deny_count = models.IntegerField()

    def __str__(self):
       return self.text

@python_2_unicode_compatible
class Treatment(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime.now())
    treatment_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)
    slots_date = models.DateTimeField(blank=True, null=True)
    slots_count = models.IntegerField(default=0)

    def __str__(self):
       return self.person.__str__()

    @property
    def websocket_group(self):
        return ChannelGroup("treatment-%s" % self.id)

    class Meta:
        permissions = (
            ("offer_treatment", "Can offer treatment"),
        )

@python_2_unicode_compatible
class Message(models.Model):
    TYPE = (
        ('S', 'Sent'),
        ('R', 'Received'),
    )

    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='messages')
    created_at = models.DateTimeField(default=datetime.datetime.now())
    external_id = models.BigIntegerField(blank=True, null=True)
    text = models.TextField()
    is_sync = models.BooleanField(default=False)
    msg_type = models.CharField(max_length=1, choices=TYPE)

    def __str__(self):
       return self.text

@python_2_unicode_compatible
class Invite(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    issue = models.OneToOneField(Issue, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=datetime.datetime.now())
    is_sync = models.BooleanField(default=False)
    sync_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
       return self.person.__str__()
