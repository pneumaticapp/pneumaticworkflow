# Generated by Django 2.2.28 on 2022-12-01 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0171_auto_20221031_1342'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='systemtemplate',
            options={'ordering': ('type', 'order')},
        ),
        migrations.AlterField(
            model_name='delay',
            name='end_date',
            field=models.DateTimeField(blank=True, help_text='The date the delay really ended(for example will be ended forced by resuming the workflow)', null=True),
        ),
        migrations.AlterField(
            model_name='systemtemplate',
            name='type',
            field=models.CharField(choices=[('generic', 'Library'), ('owner_onboarding', 'Onboarding account owners'), ('invited_onboarding_admin', 'Onboarding admin users'), ('invited_onboarding_regular', 'Onboarding non-admin users'), ('activated_template', 'Activated')], default='generic', max_length=48),
        ),
        migrations.AlterField(
            model_name='template',
            name='type',
            field=models.CharField(choices=[('user', 'custom'), ('from_library', 'library'), ('builtin_admin_onboarding', 'Onboarding admin user'), ('builtin_user_onboarding', 'Onboarding not admin user'), ('builtin_account_owner_onboarding', 'Onboarding account owner')], default='user', max_length=48),
        ),
        migrations.AlterField(
            model_name='workflow',
            name='status',
            field=models.IntegerField(choices=[(0, 'Workflow in work'), (1, 'Workflow done'), (2, 'Workflow terminated'), (3, 'Workflow delayed')], default=0),
        )
    ]