# Generated by Django 2.2.17 on 2021-03-04 12:37

from django.db import migrations


def fill_template_id_for_entities(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0106_auto_20210304_1237'),
    ]

    operations = [
        migrations.RunPython(fill_template_id_for_entities)
    ]
