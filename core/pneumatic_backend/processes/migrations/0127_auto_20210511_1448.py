# Generated by Django 2.2.17 on 2021-05-11 14:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0071_account_max_active_workflows'),
        ('processes', '0126_auto_20210511_1155'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='WorkflowTemplate',
            new_name='SystemTemplate',
        ),
    ]
