# Generated by Django 2.2 on 2024-07-24 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0120_auto_20240718_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='date_fdw',
            field=models.IntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')], default=0, verbose_name='First day of the week'),
        ),
    ]