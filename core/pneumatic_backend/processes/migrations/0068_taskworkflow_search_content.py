# Generated by Django 2.2.16 on 2020-09-21 11:36

import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0067_auto_20200917_1308'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskworkflow',
            name='search_content',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
    ]
