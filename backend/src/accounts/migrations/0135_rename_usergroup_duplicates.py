# Generated manually for renaming UserGroup duplicates before adding unique constraint

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0134_add_external_id_to_account'),
    ]

    operations = [
        migrations.RunSQL(
            """
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
            AND accounts_usergroup.id=numbered_groups.id;
            """
        ),
    ]
