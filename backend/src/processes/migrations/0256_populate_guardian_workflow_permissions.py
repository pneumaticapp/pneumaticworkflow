"""
Data migration: populate Guardian UserObjectPermission from existing
Workflow.members (→ view_workflow) and Workflow.owners (→ manage_workflow).

Processes in batches to avoid memory issues on large datasets.

NOTE: On fresh databases (e.g. test DB creation), permissions may not exist
yet (created by Django's post_migrate signal). In that case this migration
is a no-op — migration 0257 drops the M2M tables, so there's nothing to
migrate anyway.
"""

from django.db import migrations


BATCH_SIZE = 2000


def forward(apps, schema_editor):
    Workflow = apps.get_model('processes', 'Workflow')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model('guardian', 'UserObjectPermission')

    ct = ContentType.objects.get_for_model(Workflow)

    try:
        view_perm = Permission.objects.get(
            codename='view_workflow',
            content_type=ct,
        )
        manage_perm = Permission.objects.get(
            codename='manage_workflow',
            content_type=ct,
        )
    except Permission.DoesNotExist:
        # Fresh DB — permissions not yet created (post_migrate signal).
        # Nothing to migrate since M2M tables are empty on fresh DB.
        return

    # Check if M2M through tables still exist
    if not hasattr(Workflow, 'members') or not hasattr(Workflow, 'owners'):
        return

    # --- members → view_workflow ---
    through_model = Workflow.members.through
    member_qs = through_model.objects.all().values_list(
        'workflow_id', 'user_id',
    ).iterator(chunk_size=BATCH_SIZE)

    batch = []
    for workflow_id, user_id in member_qs:
        batch.append(UserObjectPermission(
            user_id=user_id,
            permission=view_perm,
            content_type=ct,
            object_pk=str(workflow_id),
        ))
        if len(batch) >= BATCH_SIZE:
            UserObjectPermission.objects.bulk_create(
                batch, ignore_conflicts=True,
            )
            batch = []
    if batch:
        UserObjectPermission.objects.bulk_create(
            batch, ignore_conflicts=True,
        )

    # --- owners → manage_workflow + view_workflow ---
    owners_through = Workflow.owners.through
    owner_qs = owners_through.objects.all().values_list(
        'workflow_id', 'user_id',
    ).iterator(chunk_size=BATCH_SIZE)

    batch = []
    for workflow_id, user_id in owner_qs:
        batch.append(UserObjectPermission(
            user_id=user_id,
            permission=manage_perm,
            content_type=ct,
            object_pk=str(workflow_id),
        ))
        batch.append(UserObjectPermission(
            user_id=user_id,
            permission=view_perm,
            content_type=ct,
            object_pk=str(workflow_id),
        ))
        if len(batch) >= BATCH_SIZE:
            UserObjectPermission.objects.bulk_create(
                batch, ignore_conflicts=True,
            )
            batch = []
    if batch:
        UserObjectPermission.objects.bulk_create(
            batch, ignore_conflicts=True,
        )


def backward(apps, schema_editor):
    """Remove all Guardian permissions for Workflow objects."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model('guardian', 'UserObjectPermission')
    Workflow = apps.get_model('processes', 'Workflow')

    ct = ContentType.objects.get_for_model(Workflow)
    perms = Permission.objects.filter(
        codename__in=('view_workflow', 'manage_workflow'),
        content_type=ct,
    )
    UserObjectPermission.objects.filter(
        permission__in=perms,
        content_type=ct,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0255_add_workflow_guardian_permissions'),
        ('guardian', '0002_generic_permissions_index'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
