# Generated by Django 2.2.17 on 2021-05-24 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0131_auto_20210513_1405'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='is_external',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='template',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='template',
            name='public_id',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]