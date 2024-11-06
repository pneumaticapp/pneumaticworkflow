# Generated by Django 2.2.12 on 2020-04-24 23:53

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('processes', '0022_remove_task_responsible'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='responsible',
            field=models.ManyToManyField(related_name='task_responsible', through='TaskComplete', to=settings.AUTH_USER_MODEL),
        ),
    ]