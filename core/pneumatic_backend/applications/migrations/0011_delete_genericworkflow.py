# Generated by Django 2.2.15 on 2020-08-28 07:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0050_delete_accountgenericworkflows'),
        ('applications', '0010_auto_20200624_1111'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GenericWorkflow',
        ),
    ]