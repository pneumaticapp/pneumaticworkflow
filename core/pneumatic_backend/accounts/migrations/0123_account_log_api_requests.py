# Generated by Django 2.2 on 2024-08-07 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0122_auto_20240726_0642'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='log_api_requests',
            field=models.BooleanField(default=False),
        ),
    ]
