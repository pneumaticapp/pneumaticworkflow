# Generated by Django 2.2.13 on 2020-06-23 17:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0040_account_applications'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accountapplication',
            old_name='are_workflow_added',
            new_name='is_workflow_added',
        ),
    ]