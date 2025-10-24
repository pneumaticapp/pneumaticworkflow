# Generated manually for renaming UserGroup duplicates before adding unique constraint

from django.db import migrations


def rename_usergroup_duplicates(apps, schema_editor):
    from django.db import connection
    
    update_query = """
        UPDATE accounts_usergroup
        SET name = CONCAT(accounts_usergroup.name, ' ', (numbered_groups.copy_number - 1))
        FROM (
          SELECT
            id,
            ROW_NUMBER() OVER (PARTITION BY name, account_id ORDER BY name) AS copy_number
          FROM accounts_usergroup
          WHERE is_deleted IS FALSE
          ORDER BY account_id
        ) AS numbered_groups
        WHERE numbered_groups.copy_number > 1
        AND accounts_usergroup.id=numbered_groups.id
    """
    
    with connection.cursor() as cursor:
        cursor.execute(update_query)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0133_account_bucket_is_public'),
    ]

    operations = [
        migrations.RunPython(
            rename_usergroup_duplicates,
            reverse_code=migrations.RunPython.noop
        ),
    ]
