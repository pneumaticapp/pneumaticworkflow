# Generated by Django 2.2 on 2023-08-11 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0107_remove_account_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='tmp_subscription',
            field=models.BooleanField(default=False, help_text='The system flag means that the temporary subscription changes is enabled and stripe webhook about changes not received yet'),
        ),
    ]