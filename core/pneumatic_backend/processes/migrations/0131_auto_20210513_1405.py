# Generated by Django 2.2.17 on 2021-05-13 14:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0130_auto_20210512_0909'),
    ]

    operations = [
        migrations.RenameField(
            model_name='process',
            old_name='is_legacy_workflow',
            new_name='is_legacy_template',
        ),
        migrations.RenameField(
            model_name='process',
            old_name='legacy_workflow_name',
            new_name='legacy_template_name',
        ),
    ]
