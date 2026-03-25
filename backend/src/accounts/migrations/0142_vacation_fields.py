from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0141_notification_text_default'),
    ]

    operations = [
        # UserGroup.type
        migrations.AddField(
            model_name='usergroup',
            name='type',
            field=models.CharField(
                choices=[
                    ('regular', 'Regular'),
                    ('personal', 'Personal'),
                ],
                default='regular',
                max_length=20,
            ),
        ),
        # User vacation fields
        migrations.AddField(
            model_name='user',
            name='absence_status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('vacation', 'On vacation'),
                    ('sick_leave', 'Sick leave'),
                ],
                default='active',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='vacation_start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='vacation_end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='vacation_substitute_group',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vacation_owner',
                to='accounts.usergroup',
            ),
        ),
        # Saved notification settings
        migrations.AddField(
            model_name='user',
            name='_saved_notify_about_tasks',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='user',
            name='_saved_is_new_tasks_subscriber',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='user',
            name='_saved_is_complete_tasks_subscriber',
            field=models.NullBooleanField(),
        ),
    ]
