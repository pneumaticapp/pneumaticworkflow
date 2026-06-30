"""Migrate Workflow ACL from M2M (members/owners) to Guardian
object-level permissions, then drop the legacy M2M fields.

Uses Django's default permissions:
  - view_workflow   (replaces members M2M)
  - change_workflow (replaces owners M2M)

Processes in batches to avoid memory issues on large datasets.
"""

from django.db import migrations


BATCH_SIZE = 2000


def forward(apps, schema_editor):
    Workflow = apps.get_model('processes', 'Workflow')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model(
        'guardian', 'UserObjectPermission',
    )

    ct = ContentType.objects.get_for_model(Workflow)

    # Ensure default permissions exist (post_migrate signal
    # has not fired yet during migration execution).
    view_perm, _ = Permission.objects.get_or_create(
        codename='view_workflow',
        content_type=ct,
        defaults={'name': 'Can view workflow'},
    )
    change_perm, _ = Permission.objects.get_or_create(
        codename='change_workflow',
        content_type=ct,
        defaults={'name': 'Can change workflow'},
    )

    # --- members → view_workflow ---
    if hasattr(Workflow, 'members'):
        through = Workflow.members.through
        rows = through.objects.all().values_list(
            'workflow_id', 'user_id',
        ).iterator(chunk_size=BATCH_SIZE)

        batch = []
        for workflow_id, user_id in rows:
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

    # --- owners → change_workflow + view_workflow ---
    if hasattr(Workflow, 'owners'):
        through = Workflow.owners.through
        rows = through.objects.all().values_list(
            'workflow_id', 'user_id',
        ).iterator(chunk_size=BATCH_SIZE)

        batch = []
        for workflow_id, user_id in rows:
            batch.append(UserObjectPermission(
                user_id=user_id,
                permission=change_perm,
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
    """Remove all Guardian workflow permissions."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model(
        'guardian', 'UserObjectPermission',
    )
    Workflow = apps.get_model('processes', 'Workflow')

    ct = ContentType.objects.get_for_model(Workflow)
    perms = Permission.objects.filter(
        codename__in=('view_workflow', 'change_workflow'),
        content_type=ct,
    )
    UserObjectPermission.objects.filter(
        permission__in=perms,
        content_type=ct,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0254_add_fileattachment_fields'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0011_update_proxy_permissions'),
        ('guardian', '0002_generic_permissions_index'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
        migrations.RemoveField(
            model_name='workflow',
            name='members',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='owners',
        ),
    ]
