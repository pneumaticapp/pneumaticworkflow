# Generated by Django 2.2.10 on 2020-03-11 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0010_auto_20200211_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='step',
            name='url',
            field=models.URLField(null=True),
        ),
        migrations.AddField(
            model_name='stepdef',
            name='url',
            field=models.URLField(null=True),
        ),
    ]
