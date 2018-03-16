from django.db import models
from django.contrib.auth.models import User, Group

from simple_history.models import HistoricalRecords

# Create your models here.
class GroupManager(models.Model):
    history = HistoricalRecords()

    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Profile(models.Model):
    history = HistoricalRecords()

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatar', blank=True, null=True)

class Person(models.Model):
    STATUS = (
        ('I', 'Identified'),
        ('N', 'Needs care'),
        ('D', 'Dispensed'),
    )

    history = HistoricalRecords()

    user_id = models.CharField(max_length=32)
    profile_image_url = models.CharField(max_length=256, blank=True, null=True)
    location = models.CharField(max_length=256, blank=True, null=True)
    friends_count = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    screen_name = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS)

    def __unicode__(self):
       return self.screen_name + ': ' + self.name


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

    def __unicode__(self):
        s = ''
        if self.person.name is not None:
            s = self.person.name + ': '
        if self.tweet_url is not None:
            s = s + self.tweet_url
        else:
            s = s + self.text
        return s

    class Meta:
        permissions = (
            ("validate_issue", "Can validate identified issues"),
        )

class Track(models.Model):
    history = HistoricalRecords()

    phrase = models.CharField(max_length=32)

    def __unicode__(self):
       return self.phrase

class TweetBlackList(models.Model):
    history = HistoricalRecords()

    text = models.CharField(max_length=560)
    deny_count = models.IntegerField()

    def __unicode__(self):
       return self.text

class Treatment(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)

    def __unicode__(self):
       return self.person.__unicode__()

    class Meta:
        permissions = (
            ("offer_treatment", "Can offer treatment"),
        )

class Message(models.Model):
    TYPE = (
        ('S', 'Sent'),
        ('R', 'Received'),
    )

    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    external_id = models.CharField(max_length=32)
    text = models.TextField()
    is_sync = models.BooleanField(default=False)
    msg_type = models.CharField(max_length=1, choices=TYPE)
