# Generated by Django 3.2.14 on 2022-08-17 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facade', '0011_rename_type_node_kind'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='allow_auto_request',
            field=models.BooleanField(default=False, help_text='Allow automatic requests for this reservation'),
        ),
    ]