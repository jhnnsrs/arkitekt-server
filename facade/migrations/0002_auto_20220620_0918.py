# Generated by Django 3.2.12 on 2022-06-20 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facade', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='node',
            name='repository, interface, cannot be the same',
        ),
        migrations.AddConstraint(
            model_name='node',
            constraint=models.UniqueConstraint(fields=('package', 'interface'), name='package, interface, cannot be the same'),
        ),
    ]