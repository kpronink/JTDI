import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
sys.path.append('G:\Work\python\JTDI\mysite\settings.py')

import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import redirect

from JtdiTASKS.models import Task


def send_digest():
    users = User.objects.filter(email__exact='')
    for user in users:
        currentdate = datetime.datetime.today()
        start_day = currentdate.combine(currentdate, currentdate.min.time())
        end_day = currentdate.combine(currentdate, currentdate.max.time())
        first_day = datetime.date(1001, 1, 1)

        tasks_overdue = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
            .filter(date_time__range=(first_day, start_day)) \
            .order_by('date', 'priority', 'time')

        tasks_today = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
            .filter(date_time__range=(start_day, end_day)) \
            .order_by('date', 'priority', 'time')
        body_mail = '<h1> Задачи на сегодня </h1>'
        for task in tasks_today:
            body_mail = body_mail + '\n<a href=' + redirect('task_detail', task.pk) + '>' + task.title + '</a>'

        body_mail = body_mail + '<h1> Просроченые задачи </h1>'
        for task in tasks_overdue:
            body_mail = body_mail + '\n<a href=' + redirect('task_detail', task.pk) + '>' + task.title + '</a>'

        send_mail('Дайджест задач', body_mail, settings.EMAIL_HOST_USER, [user.email])


send_digest()