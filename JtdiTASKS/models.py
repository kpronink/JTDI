import os
import random

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.utils import timezone


def avatar_upload_to(instance, filename):
    return os.path.join('media', instance.user.username + os.path.splitext(filename)[1])


class Project(models.Model):
    author = models.ForeignKey('auth.User')
    title = models.CharField(max_length=200, null=True)
    color_project = models.CharField(max_length=10)
    group = models.BooleanField(default=False)

    def publish(self):
        self.save()

    def __str__(self):
        return self.title


class Profile(models.Model):
    """User with app settings."""
    MALE = 'MALE'
    FEMALE = 'FEMALE'

    SEX_CHOISE = (
        (MALE, 'Мужской'),
        (FEMALE, 'Женский'))

    DDMMYYY = 'DD-MM-YYYY'
    MMDDYYY = 'MM-DD-YYYY'

    FORMAT_DATE_CHOISE = (
        (DDMMYYY, 'DD-MM-YYYY'),
        (MMDDYYY, 'MM-DD-YYYY'),
    )

    MONDAY = 'Понедельник'
    TUESDAY = 'Вторник'
    WEDNESDAY = 'Среда'
    THURSDAY = 'Четверг'
    FRIDAY = 'Пятница'
    SATURDAY = 'Суббота'
    SUNDAY = 'Воскресенье'

    FIRST_DAY_WEEEK = (
        (MONDAY, 'Понедельник'),
        (TUESDAY, 'Вторник'),
        (WEDNESDAY, 'Среда'),
        (THURSDAY, 'Четверг'),
        (FRIDAY, 'Пятница'),
        (SATURDAY, 'Суббота'),
        (SUNDAY, 'Воскресенье'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    timezone = models.CharField(max_length=50, default='Europe/London',
                                blank=True)
    formatdate = models.CharField(max_length=20, choices=FORMAT_DATE_CHOISE,
                                  default=DDMMYYY, blank=True)
    firstdayweek = models.CharField(max_length=20, choices=FIRST_DAY_WEEEK,
                                    default=MONDAY, blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOISE,
                           default=MALE, blank=True)

    avatar = models.ImageField(upload_to='avatars',
                               null=True, blank=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, created, **kwargs):
        user = instance
        '''if created:
            profile = Profile(user=user)
            profile.save()'''
        instance.profile.save()


class Task(models.Model):
    PRIORITY_1 = '1'
    PRIORITY_2 = '2'
    PRIORITY_3 = '3'
    PRIORITY_4 = '4'

    PRIORITY_CHOISE = (
        (PRIORITY_1, 'Приоритет 1'),
        (PRIORITY_2, 'Приоритет 2'),
        (PRIORITY_3, 'Приоритет 3'),
        (PRIORITY_4, 'Приоритет 4'))

    author = models.ForeignKey('auth.User')
    performer = models.ForeignKey('auth.User', related_name='performer', blank=True, null=True)
    project = models.ForeignKey('Project', null=True, default=None,
                                blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000, blank=True)
    repeating = models.BooleanField(default=False, blank=True)
    date = models.DateField(default=timezone.now, blank=True, null=True)
    time = models.TimeField(default=timezone.now, blank=True, null=True)
    date_finish = models.DateField(default=None, blank=True, null=True)
    date_time_finish = models.DateTimeField(default=None, blank=True, null=True)
    planed_date_finish = models.DateField(default=None, blank=True, null=True)
    active = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    group = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOISE,
                                default=PRIORITY_4, blank=True)
    color = models.CharField(max_length=20, default='grey', blank=True)
    
    remind = models.BooleanField(default=True)

    def publish(self):
        self.published_date = timezone.now
        self.save()

    def __str__(self):
        return self.title


class PartnerGroup(models.Model):

    project = models.ForeignKey('Project', default=None)
    partner = models.ForeignKey('auth.User')


class InviteUser(models.Model):

    user_sender = models.ForeignKey('auth.User', related_name='user_sender')
    user_invite = models.ForeignKey('auth.User', related_name='user_invite')
    invited = models.BooleanField(default=False)
    not_invited = models.BooleanField(default=False)
