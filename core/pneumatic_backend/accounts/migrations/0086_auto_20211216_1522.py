# Generated by Django 2.2.24 on 2021-12-16 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0085_notification_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='plan',
            field=models.CharField(choices=[('free', 'free'), ('trial', 'trial'), ('premium', 'premium')], default='free', max_length=10),
        ),
        migrations.AddField(
            model_name='account',
            name='plan_expiration',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
