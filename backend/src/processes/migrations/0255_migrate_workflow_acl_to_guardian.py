"""Migrate Workflow ACL from M2M (members/owners) to Guardian
object-level permissions, then drop the legacy M2M fields.

Uses Django's default permissions:
  - view_workflow   (replaces members M2M)
  - change_workflow (replaces owners M2M)

Members are classified by source so surgical revoke still works:
  - active TaskPerformer USER  → Performer (source_id=task_id)
  - active TaskPerformer GROUP → PerformerGroup (source_id=group_id)
  - remaining members          → WorkflowViewer (legacy / mentions)
  - owners                     → TemplateOwner (+ change_workflow)

Processes in batches to avoid memory issues on large datasets.
"""

from django.db import migrations
from django.db.models import F
# Hardcoded to avoid importing from app code — migration must be
# immune to future changes in PermissionSource / enum values.
SOURCE_WORKFLOW_VIEWER = 'WorkflowViewer'
SOURCE_TEMPLATE_OWNER = 'TemplateOwner'
SOURCE_PERFORMER = 'Performer'
SOURCE_PERFORMER_GROUP = 'PerformerGroup'
PERFORMER_TYPE_USER = 'user'
PERFORMER_TYPE_GROUP = 'group'
DIRECTLY_DELETED = 1

BATCH_SIZE = 2000


def _flush(UserObjectPermission, batch):
    if batch:
        UserObjectPermission.objects.bulk_create(
            batch, ignore_conflicts=True,
        )
    return []


def forward(apps, schema_editor):
    Workflow = apps.get_model('processes', 'Workflow')
    TaskPerformer = apps.get_model('processes', 'TaskPerformer')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model(
        'permissions', 'UserObjectPermission',
    )
    UserGroup = apps.get_model('accounts', 'UserGroup')

    ct, _ = ContentType.objects.get_or_create(
        app_label='processes', model='workflow',
    )
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

    # (workflow_id, user_id) covered by PERFORMER* or owners —
    # must not also get WORKFLOW_VIEWER from members, otherwise
    # remove-performer / remove-owner cannot revoke view.
    covered = set()
    if hasattr(Workflow, 'owners'):
        covered.update(
            Workflow.owners.through.objects.values_list(
                'workflow_id', 'user_id',
            ),
        )

    # --- active USER performers → Performer ---
    user_rows = (
        TaskPerformer.objects
        .filter(type=PERFORMER_TYPE_USER)
        .exclude(directly_status=DIRECTLY_DELETED)
        .exclude(user_id__isnull=True)
        .values_list('task_id', 'task__workflow_id', 'user_id')
        .iterator(chunk_size=BATCH_SIZE)
    )
    batch = []
    for task_id, workflow_id, user_id in user_rows:
        covered.add((workflow_id, user_id))
        batch.append(UserObjectPermission(
            user_id=user_id,
            permission=view_perm,
            content_type=ct,
            object_pk=str(workflow_id),
            source_type=SOURCE_PERFORMER,
            source_id=int(task_id),
        ))
        if len(batch) >= BATCH_SIZE:
            batch = _flush(UserObjectPermission, batch)
    batch = _flush(UserObjectPermission, batch)

    # --- active GROUP performers → PerformerGroup ---
    group_rows = (
        TaskPerformer.objects
        .filter(type=PERFORMER_TYPE_GROUP)
        .exclude(directly_status=DIRECTLY_DELETED)
        .exclude(group_id__isnull=True)
        .values_list('task__workflow_id', 'group_id')
        .iterator(chunk_size=BATCH_SIZE)
    )
    # Deduplicate (workflow_id, group_id) — same group on many tasks
    # still uses one PERFORMER_GROUP source_id=group_id per workflow.
    wf_groups = set()
    for workflow_id, group_id in group_rows:
        wf_groups.add((workflow_id, group_id))

    group_ids = {gid for _, gid in wf_groups}
    group_members = {}
    if group_ids:
        active_group_ids = set(
            UserGroup.objects.filter(
                id__in=group_ids,
                is_deleted=False,
            ).values_list('id', flat=True),
        )
        through = UserGroup.users.through
        for gid, uid in (
            through.objects
            .filter(usergroup_id__in=active_group_ids)
            .values_list('usergroup_id', 'user_id')
            .iterator(chunk_size=BATCH_SIZE)
        ):
            group_members.setdefault(gid, set()).add(uid)

    batch = []
    for workflow_id, group_id in wf_groups:
        for user_id in group_members.get(group_id, ()):
            covered.add((workflow_id, user_id))
            batch.append(UserObjectPermission(
                user_id=user_id,
                permission=view_perm,
                content_type=ct,
                object_pk=str(workflow_id),
                source_type=SOURCE_PERFORMER_GROUP,
                source_id=int(group_id),
            ))
            if len(batch) >= BATCH_SIZE:
                batch = _flush(UserObjectPermission, batch)
    batch = _flush(UserObjectPermission, batch)

    # --- remaining members → WorkflowViewer (mentions / legacy) ---
    if hasattr(Workflow, 'members'):
        through = Workflow.members.through
        rows = through.objects.all().values_list(
            'workflow_id', 'user_id',
        ).iterator(chunk_size=BATCH_SIZE)

        batch = []
        for workflow_id, user_id in rows:
            if (workflow_id, user_id) in covered:
                continue
            batch.append(UserObjectPermission(
                user_id=user_id,
                permission=view_perm,
                content_type=ct,
                object_pk=str(workflow_id),
                source_type=SOURCE_WORKFLOW_VIEWER,
                source_id=int(workflow_id),
            ))
            if len(batch) >= BATCH_SIZE:
                batch = _flush(UserObjectPermission, batch)
        batch = _flush(UserObjectPermission, batch)

    # --- owners → change_workflow + view_workflow (TemplateOwner) ---
    if hasattr(Workflow, 'owners'):
        through = Workflow.owners.through
        rows = through.objects.annotate(
            template_id=F('workflow__template_id'),
        ).values_list(
            'workflow_id', 'user_id', 'template_id',
        ).iterator(chunk_size=BATCH_SIZE)

        batch = []
        for workflow_id, user_id, template_id in rows:
            sid = int(template_id) if template_id else 0
            batch.append(UserObjectPermission(
                user_id=user_id,
                permission=change_perm,
                content_type=ct,
                object_pk=str(workflow_id),
                source_type=SOURCE_TEMPLATE_OWNER,
                source_id=sid,
            ))
            batch.append(UserObjectPermission(
                user_id=user_id,
                permission=view_perm,
                content_type=ct,
                object_pk=str(workflow_id),
                source_type=SOURCE_TEMPLATE_OWNER,
                source_id=sid,
            ))
            if len(batch) >= BATCH_SIZE:
                batch = _flush(UserObjectPermission, batch)
        batch = _flush(UserObjectPermission, batch)


def backward(apps, schema_editor):
    """Remove all Guardian workflow permissions."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model(
        'permissions', 'UserObjectPermission',
    )

    ct, _ = ContentType.objects.get_or_create(
        app_label='processes', model='workflow',
    )
    perms = Permission.objects.filter(
        codename__in=('view_workflow', 'change_workflow'),
        content_type=ct,
    )

    # Batch delete
    while True:
        ids = list(
            UserObjectPermission.objects.filter(
                permission__in=perms,
                content_type=ct,
            ).values_list('id', flat=True)[:BATCH_SIZE]
        )
        if not ids:
            break
        UserObjectPermission.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0254_add_fileattachment_fields'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0011_update_proxy_permissions'),
        ('permissions', '0002_user_object_permission'),
        ('accounts', '0124_delete_group_add_usergroup'),
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
