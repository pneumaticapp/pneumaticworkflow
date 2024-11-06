# Generated by Django 2.2.16 on 2020-10-22 10:02

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0082_auto_20201022_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflowtemplate',
            name='workflow_template',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='<span style="float: right;">If you want to pass default args to kickoff fields, add default parameter to field template like this: `"default": "account_name"`. Possible dynamic values: account_name, user_first_name, user_last_name, user_email</span>', null=True),
        ),
    ]