# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-16 16:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('photos', '0001_initial'), ('photos', '0003_remove_cecbrprofile__cecbr_salt'), ('photos', '0004_cecbrprofile__cecbr_salt'), ('photos', '0005_auto_20170816_1156')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CECBRProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('_cecbr_pwd_set', models.BooleanField(default=False)),
                ('cecbr_uname', models.CharField(blank=True, max_length=128)),
                ('cecbr_password', models.CharField(blank=True, max_length=256)),
                ('last_album_view', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('_cecbr_salt', models.BinaryField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
