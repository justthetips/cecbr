# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-16 15:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cecbrprofile',
            name='_cecbr_salt',
        ),
    ]
