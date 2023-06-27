# Generated by Django 3.2.19 on 2023-06-09 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facade', '0016_alter_node_is_test_for'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='is_test_for',
            field=models.ManyToManyField(blank=True, help_text='The users that have pinned the position', related_name='tests', to='facade.Node'),
        ),
    ]
