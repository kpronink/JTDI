# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-03 03:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('JtdiTASKS', '0009_profile_mail_notify'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='firstdayweek',
            new_name='day_week',
        ),
    ]
