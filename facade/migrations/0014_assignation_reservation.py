# Generated by Django 3.1.7 on 2021-03-22 09:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facade', '0013_reservation'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignation',
            name='reservation',
            field=models.ForeignKey(blank=True, help_text='Which reservation are we assigning to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assignations', to='facade.reservation'),
        ),
    ]
