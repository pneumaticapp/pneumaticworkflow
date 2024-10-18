from django.db import migrations


def migrate_user_to_invite(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    users = User.objects.filter(is_deleted=False, is_account_owner=False)

    for user in users:
        invite = user.invite
        if invite:
            invite.invited_user = user
            invite.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0058_auto_20201124_1056'),
    ]

    operations = [
        migrations.RunPython(migrate_user_to_invite, reverse_code=migrations.RunPython.noop)
    ]
