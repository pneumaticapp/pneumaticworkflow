"""Migrate manage_workflow → change_workflow in Guardian permissions.

Django may have already auto-created 'change_workflow' from
default_permissions, so we can't simply UPDATE the codename
(unique constraint violation). Instead we:

1. Get or create the 'change_workflow' Permission row.
2. Re-point all Guardian UserObjectPermission rows from the old
   manage_workflow permission_id to the change_workflow permission_id.
3. Delete the now-orphaned manage_workflow Permission.
4. Ensure all 4 standard permissions exist (add/view/change/delete).
"""

from django.db import migrations


def rename_manage_to_change(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    UserObjectPermission = apps.get_model('guardian', 'UserObjectPermission')

    ct = ContentType.objects.get(
        app_label='processes', model='workflow',
    )

    old_perm = Permission.objects.filter(
        codename='manage_workflow',
        content_type=ct,
    ).first()

    if not old_perm:
        # Already migrated or never existed — nothing to do
        return

    # Get or create the target permission
    new_perm, _created = Permission.objects.get_or_create(
        codename='change_workflow',
        content_type=ct,
        defaults={'name': 'Can change workflow'},
    )

    # Re-point Guardian rows from old → new permission.
    # Use raw SQL to handle potential duplicates gracefully:
    # if a user already has change_workflow on the same object,
    # we skip that row and just delete the old one.
    db_alias = schema_editor.connection.alias

    # 1. Update rows that won't cause duplicates
    #    (user doesn't already have change_workflow on that object)
    UserObjectPermission.objects.using(db_alias).filter(
        permission=old_perm,
    ).exclude(
        # Exclude rows where user already has the new permission
        # on the same object (would violate unique_together)
        user_id__in=UserObjectPermission.objects.using(db_alias).filter(
            permission=new_perm,
        ).values('user_id'),
    ).update(permission=new_perm)

    # 2. Delete remaining old-perm rows (duplicates that couldn't
    #    be updated because the user already has change_workflow)
    UserObjectPermission.objects.using(db_alias).filter(
        permission=old_perm,
    ).delete()

    # 3. Remove the orphaned manage_workflow permission
    old_perm.delete()

    # 4. Ensure all 4 standard Django permissions exist
    for codename, name in [
        ('add_workflow', 'Can add workflow'),
        ('view_workflow', 'Can view workflow'),
        ('change_workflow', 'Can change workflow'),
        ('delete_workflow', 'Can delete workflow'),
    ]:
        Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={'name': name},
        )


def revert_change_to_manage(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    UserObjectPermission = apps.get_model('guardian', 'UserObjectPermission')

    ct = ContentType.objects.get(
        app_label='processes', model='workflow',
    )

    change_perm = Permission.objects.filter(
        codename='change_workflow',
        content_type=ct,
    ).first()

    if not change_perm:
        return

    # Re-create manage_workflow
    old_perm, _ = Permission.objects.get_or_create(
        codename='manage_workflow',
        content_type=ct,
        defaults={'name': 'Can manage workflow lifecycle'},
    )

    # Move Guardian rows back
    db_alias = schema_editor.connection.alias
    UserObjectPermission.objects.using(db_alias).filter(
        permission=change_perm,
    ).update(permission=old_perm)


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0258_fix_workflow_default_permissions'),
    ]

    operations = [
        migrations.RunPython(
            rename_manage_to_change,
            revert_change_to_manage,
        ),
    ]
