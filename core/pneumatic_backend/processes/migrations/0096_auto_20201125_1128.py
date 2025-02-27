# Generated by Django 2.2.16 on 2020-11-25 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0095_merge_20201117_0839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflow',
            name='type',
            field=models.CharField(choices=[('user', 'custom'), ('from_library', 'generic'), ('builtin_admin_onboarding', 'Invited admin users onboarding workflow'), ('builtin_user_onboarding', 'Invited regular users onboarding workflow'), ('builtin_account_owner_onboarding', 'Owner onboarding')], default='user', max_length=48),
        ),
    ]
