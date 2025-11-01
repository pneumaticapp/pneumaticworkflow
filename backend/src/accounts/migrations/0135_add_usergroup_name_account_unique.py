# Generated manually for adding unique constraint to UserGroup

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0134_rename_usergroup_duplicates'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='usergroup',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False),
                fields=['name', 'account'],
                name='usergroup_name_account_unique',
            ),
        ),
    ]
