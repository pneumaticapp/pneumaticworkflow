# Generated by Django 2.2.17 on 2021-04-07 12:02
from django.db import migrations


def forwards(apps, schema_editor):
    pass


def backwards(*args, **kwards):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0117_auto_20210412_0918'),
    ]

    operations = [
        migrations.RunPython(
            code=forwards,
            reverse_code=backwards,
            atomic=True
        )
    ]