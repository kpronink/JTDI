# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-19 10:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('JtdiTASKS', '0004_taskstimetracker'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.CharField(blank=True, choices=[('Wait', 'Ожидание'), ('Started', 'Выполнение'), ('Stoped', 'Приостановлена'), ('Finished', 'Завершена')], default='Wait', max_length=20),
        ),
    ]