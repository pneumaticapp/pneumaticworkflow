# Generated by Django 2.2.14 on 2020-08-10 12:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0051_delete_aborted_processes'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='status_updated',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]