# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-16 15:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0003_remove_cecbrprofile__cecbr_salt'),
    ]

    operations = [
        migrations.AddField(
            model_name='cecbrprofile',
            name='_cecbr_salt',
            field=models.BinaryField(blank=True),
        ),
    ]
