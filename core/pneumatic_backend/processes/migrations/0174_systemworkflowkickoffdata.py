# Generated by Django 2.2.28 on 2022-12-13 10:31

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import pneumatic_backend.generics.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0173_delay_directly_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemWorkflowKickoffData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=255)),
                ('user_role', models.CharField(choices=[('owner_onboarding', 'Onboarding account owners'), ('invited_onboarding_admin', 'Onboarding admin users'), ('invited_onboarding_regular', 'Onboarding non-admin users')], max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('kickoff_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='<span style="float: right; line-height: 18px; font-size: 15px; color: #4C4C4C">You can use template vars: <b>account_name, user_first_name, user_last_name, user_email</b></br>Example: Onboarding {{ user_first_name }} {{ user_first_name }}</span>', null=True)),
                ('system_template', models.ForeignKey(
                        limit_choices_to={
                            'type': 'activated_template',
                            'is_active': True
                        },
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='system_workflow_kickoff_data',
                        to='processes.SystemTemplate'
                    )
                ),
            ],
            options={
                'ordering': ('user_role', 'order'),
            },
            bases=(pneumatic_backend.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
    ]
