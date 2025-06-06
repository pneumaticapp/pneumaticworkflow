# Generated by Django 2.2.26 on 2023-02-01 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0093_remove_notification_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='lease_level',
            field=models.CharField(choices=[('standard', 'standard'), ('partner', 'partner'), ('tenant', 'tenant')], default='standard', max_length=50),
        ),
        migrations.AddField(
            model_name='account',
            name='logo_lg',
            field=models.URLField(max_length=1024, null=True, help_text='340px x 96px'),
        ),
        migrations.AddField(
            model_name='account',
            name='logo_sm',
            field=models.URLField(max_length=1024, null=True, help_text='80px x 80px'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('system', 'system'), ('onboarding', 'onboarding not finished'), ('comment', 'new comment'), ('mention', 'mention'), ('urgent', 'urgent'), ('not_urgent', 'not urgent'), ('overdue_task', 'overdue task'), ('snooze_workflow', 'snooze workflow'), ('resume_workflow', 'resume workflow')], max_length=24),
        ),
        migrations.AddField(
            model_name='account',
            name='master_account',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tenants',
                to='accounts.Account'
            ),
        ),
        migrations.AlterField(
            model_name='account',
            name='name',
            field=models.TextField(
                default='Company name',
                verbose_name='Company name'
            ),
        ),
    ]
