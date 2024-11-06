# Generated by Django 2.2.26 on 2023-03-09 11:30

from django.db import migrations, models
from django.core.cache import cache


def clear_partners_cache(apps, schema_editor):
    account_cls = apps.get_model('accounts', 'Account')
    for account in account_cls.objects.filter(
            lease_level='partner',
            is_deleted=False
    ):
        cache.delete(f'account:{account.id}')


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0097_account_trial_ended'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='tenants_active_users',
            field=models.IntegerField(default=0),
        ),
        migrations.RunSQL("""
            WITH accounts AS (
              SELECT
                aa.id,
                COUNT(au.id) AS active_users
              FROM accounts_user au
                INNER JOIN accounts_account aa
                  ON au.account_id = aa.id
              WHERE au.status = 'active'
                AND au.type = 'user'
                AND au.is_deleted IS FALSE
                AND aa.is_deleted IS FALSE
                AND aa.lease_level = 'partner'
              GROUP BY aa.id
            )
            UPDATE accounts_account SET active_users=accounts.active_users
            FROM accounts
            WHERE accounts_account.id=accounts.id
        """),
        migrations.RunSQL("""
            WITH tenant AS (
              SELECT
                master_account_id AS id,
                SUM(tenant.active_users) AS tenants_active_users
              FROM accounts_account tenant
              WHERE tenant.lease_level = 'tenant'
                AND tenant.is_deleted IS FALSE
                AND master_account_id IS NOT NULL
              GROUP BY master_account_id
            )
    
            UPDATE accounts_account 
              SET tenants_active_users = tenant.tenants_active_users
            FROM tenant
            WHERE accounts_account.id=tenant.id
        """),
        migrations.RunPython(
            code=clear_partners_cache,
            reverse_code=migrations.RunPython.noop
        )
    ]