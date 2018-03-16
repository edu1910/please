from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from django.forms.widgets import ClearableFileInput
from django.db import models

from .models import GroupManager, Profile, Person, Issue, Track, TweetBlackList, Treatment, Message

# Register your models here.
@admin.register(GroupManager)
class GroupManagerAdmin(admin.ModelAdmin):
    pass

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ImageField: {'widget': ClearableFileInput},
    }

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    pass

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    pass

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    pass

@admin.register(TweetBlackList)
class TweetBlackListAdmin(admin.ModelAdmin):
    pass

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    pass

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass

# Register your models here.
class GroupManagerInline(admin.StackedInline):
    model = GroupManager
    can_delete = True
    verbose_name_plural = 'managers'

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profiles'
    formfield_overrides = {
        models.ImageField: {'widget': ClearableFileInput},
    }

class GroupAdmin(BaseGroupAdmin):
    inlines = (GroupManagerInline,)

class UserAdmin(BaseUserAdmin):
    formfield_overrides = {
        models.ImageField: {'widget': ClearableFileInput},
    }
    inlines = (ProfileInline,)

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
