# Generated by Django 3.1.7 on 2021-03-04 14:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('facade', '0006_auto_20210304_1213'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='parent',
        ),
    ]
