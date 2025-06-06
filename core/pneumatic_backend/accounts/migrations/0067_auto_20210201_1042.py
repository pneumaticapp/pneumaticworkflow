# Generated by Django 2.2.17 on 2021-02-01 10:42

from django.db import migrations

from pneumatic_backend.authentication.tokens import PneumaticToken
from pneumatic_backend.executor import RawSqlExecutor


def delete_robots(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.filter(is_deleted=False, is_robot=True):
        PneumaticToken.expire_all_tokens(user)

    RawSqlExecutor.execute(
        """
        DELETE FROM accounts_group_users 
        WHERE user_id IN (
          SELECT id FROM accounts_user WHERE first_name = 'Robot'
        )
        """, ()
    )
    RawSqlExecutor.execute(
        """
        DELETE FROM accounts_group 
        WHERE name IN (
          SELECT email FROM accounts_user WHERE first_name = 'Robot'
        )
        """, ()
    )
    RawSqlExecutor.execute(
        """
        DELETE FROM accounts_apilogs WHERE key_id IN (
            SELECT id FROM accounts_apikey WHERE user_id IN (
              SELECT id FROM accounts_user WHERE first_name = 'Robot'
        ))
        """, ()
    )
    RawSqlExecutor.execute(
        """
        DELETE FROM accounts_apikey WHERE user_id IN (
          SELECT id FROM accounts_user WHERE first_name = 'Robot'
        )
        """, ()
    )
    RawSqlExecutor.execute(
        """
        DELETE FROM processes_taskresponsible WHERE user_id IN (
          SELECT id FROM accounts_user WHERE first_name = 'Robot'
        )
        """, ()
    )
    RawSqlExecutor.execute(
        """DELETE FROM processes_taskworkflow_responsible WHERE user_id IN (
          SELECT id FROM accounts_user WHERE first_name = 'Robot'
        )""", ()
    )
    User.objects.raw('DELETE FROM accounts_user WHERE is_robot IS TRUE;')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0066_user_is_notified_about_notifications'),
    ]

    operations = [
        migrations.RunPython(
            delete_robots,
            reverse_code=migrations.RunPython.noop
        )
    ]
