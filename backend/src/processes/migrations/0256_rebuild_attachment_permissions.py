"""Rebuild access_attachment permissions for all restricted attachments.

Migration 0255 migrated workflow-level ACL (members/owners M2M) to
Guardian view_workflow/change_workflow UOP records, but did not rebuild
the file-level access_attachment UOP/GOP records.

If the file migration (migrate_file_attachment_to_attachment) was
executed before 0255, WorkflowPermissionService.get_users_with_view()
returned empty sets — so access_attachment was only granted to direct
task performers, not to workflow viewers or template owners.

This migration performs a full recalculation of access_attachment for
every restricted Attachment, using the now-correct Guardian viewer set.
"""

from django.db import migrations
from django.db.models import Q

SOURCE_PERFORMER = 'Performer'
SOURCE_PERFORMER_GROUP = 'PerformerGroup'
SOURCE_TEMPLATE_OWNER = 'TemplateOwner'
SOURCE_WORKFLOW_VIEWER = 'WorkflowViewer'
PERFORMER_TYPE_USER = 'user'
PERFORMER_TYPE_GROUP = 'group'
OWNER_TYPE_USER = 'user'
OWNER_TYPE_GROUP = 'group'
DIRECTLY_DELETED = 1
ACCESS_RESTRICTED = 'restricted'
SOURCE_TYPE_TASK = 'Task'
SOURCE_TYPE_WORKFLOW = 'Workflow'
SOURCE_TYPE_TEMPLATE = 'Template'

BATCH_SIZE = 500


def _get_workflow_viewer_ids(
    UserObjectPermission, view_perm, wf_ct, workflow_id,
):
    """User IDs with view_workflow on a given workflow."""
    return set(
        UserObjectPermission.objects.filter(
            permission=view_perm,
            content_type=wf_ct,
            object_pk=str(workflow_id),
        ).values_list('user_id', flat=True),
    )


def _get_template_owners(TemplateOwner, template_id):
    """Returns (user_ids, group_ids) for active template owners."""
    user_ids = set()
    group_ids = set()
    for owner in TemplateOwner.objects.filter(
        template_id=template_id,
        is_deleted=False,
    ).only('id', 'type', 'user_id', 'group_id'):
        if owner.type == OWNER_TYPE_USER and owner.user_id:
            user_ids.add((owner.user_id, owner.pk))
        elif owner.type == OWNER_TYPE_GROUP and owner.group_id:
            group_ids.add(owner.group_id)
    return user_ids, group_ids


def _rebuild_task_attachment(
    att, task, workflow,
    UserObjectPermission, GroupObjectPermission,
    att_ct, att_perm, wf_ct, view_perm,
    TaskPerformer, TemplateOwner,
):
    """Rebuild access_attachment for a TASK-sourced attachment."""
    obj_pk = str(att.pk)

    user_rows = []
    group_ids = set()

    performers = (
        TaskPerformer.objects
        .filter(task_id=task.id)
        .exclude(directly_status=DIRECTLY_DELETED)
    )
    for perf in performers:
        if perf.user_id and perf.type == PERFORMER_TYPE_USER:
            user_rows.append((
                perf.user_id, SOURCE_PERFORMER, perf.pk,
            ))
        if perf.group_id and perf.type == PERFORMER_TYPE_GROUP:
            group_ids.add(perf.group_id)

    if workflow:
        viewer_ids = _get_workflow_viewer_ids(
            UserObjectPermission, view_perm, wf_ct, workflow.id,
        )
        for uid in viewer_ids:
            user_rows.append((
                uid, SOURCE_WORKFLOW_VIEWER, workflow.id,
            ))

        if workflow.template_id:
            owner_users, owner_groups = _get_template_owners(
                TemplateOwner, workflow.template_id,
            )
            for uid, owner_pk in owner_users:
                user_rows.append((
                    uid, SOURCE_TEMPLATE_OWNER, owner_pk,
                ))
            group_ids |= owner_groups

    return obj_pk, user_rows, group_ids


def _rebuild_workflow_attachment(
    att, workflow,
    UserObjectPermission, GroupObjectPermission,
    att_ct, att_perm, wf_ct, view_perm,
    TaskPerformer, TemplateOwner, Task,
):
    """Rebuild access_attachment for a WORKFLOW-sourced attachment."""
    obj_pk = str(att.pk)
    user_rows = []
    group_ids = set()

    task_ids = list(
        Task.objects.filter(
            workflow_id=workflow.id,
            is_deleted=False,
        ).values_list('id', flat=True),
    )
    if task_ids:
        performers = (
            TaskPerformer.objects
            .filter(task_id__in=task_ids)
            .exclude(directly_status=DIRECTLY_DELETED)
        )
        for perf in performers:
            if perf.user_id and perf.type == PERFORMER_TYPE_USER:
                user_rows.append((
                    perf.user_id, SOURCE_PERFORMER, perf.pk,
                ))
            if perf.group_id and perf.type == PERFORMER_TYPE_GROUP:
                group_ids.add(perf.group_id)

    viewer_ids = _get_workflow_viewer_ids(
        UserObjectPermission, view_perm, wf_ct, workflow.id,
    )
    for uid in viewer_ids:
        user_rows.append((
            uid, SOURCE_WORKFLOW_VIEWER, workflow.id,
        ))

    if workflow.template_id:
        owner_users, owner_groups = _get_template_owners(
            TemplateOwner, workflow.template_id,
        )
        for uid, owner_pk in owner_users:
            user_rows.append((
                uid, SOURCE_TEMPLATE_OWNER, owner_pk,
            ))
        group_ids |= owner_groups

    return obj_pk, user_rows, group_ids


def forward(apps, schema_editor):
    Attachment = apps.get_model('storage', 'Attachment')
    Workflow = apps.get_model('processes', 'Workflow')
    Task = apps.get_model('processes', 'Task')
    TaskPerformer = apps.get_model('processes', 'TaskPerformer')
    TemplateOwner = apps.get_model('processes', 'TemplateOwner')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    UserObjectPermission = apps.get_model(
        'permissions', 'UserObjectPermission',
    )
    GroupObjectPermission = apps.get_model(
        'permissions', 'GroupObjectPermission',
    )

    att_ct, _ = ContentType.objects.get_or_create(
        app_label='storage', model='attachment',
    )
    wf_ct, _ = ContentType.objects.get_or_create(
        app_label='processes', model='workflow',
    )
    att_perm, _ = Permission.objects.get_or_create(
        codename='access_attachment',
        content_type=att_ct,
        defaults={'name': 'Can access attachment'},
    )
    view_perm, _ = Permission.objects.get_or_create(
        codename='view_workflow',
        content_type=wf_ct,
        defaults={'name': 'Can view workflow'},
    )

    restricted_atts = (
        Attachment.objects
        .filter(access_type=ACCESS_RESTRICTED, is_deleted=False)
        .select_related('task', 'workflow', 'event')
    )

    processed = 0
    user_batch = []
    group_batch = []

    for att in restricted_atts.iterator(chunk_size=BATCH_SIZE):
        workflow = att.workflow
        if not workflow and att.task_id:
            task = att.task
            workflow = (
                Workflow.objects.filter(
                    id=task.workflow_id,
                    is_deleted=False,
                ).first()
                if task and task.workflow_id else None
            )
        if not workflow and att.event_id:
            event = att.event
            workflow = (
                Workflow.objects.filter(
                    id=event.workflow_id,
                    is_deleted=False,
                ).first()
                if event and event.workflow_id else None
            )
        if not workflow:
            continue

        if workflow.is_deleted:
            continue

        obj_pk = str(att.pk)

        # Clear existing access_attachment for this attachment
        UserObjectPermission.objects.filter(
            content_type=att_ct,
            permission=att_perm,
            object_pk=obj_pk,
        ).delete()
        GroupObjectPermission.objects.filter(
            content_type=att_ct,
            permission=att_perm,
            object_pk=obj_pk,
        ).delete()

        user_rows = []
        group_ids = set()

        if att.source_type == SOURCE_TYPE_TASK:
            task = att.task
            if not task:
                continue
            _, user_rows, group_ids = _rebuild_task_attachment(
                att, task, workflow,
                UserObjectPermission, GroupObjectPermission,
                att_ct, att_perm, wf_ct, view_perm,
                TaskPerformer, TemplateOwner,
            )
        elif att.source_type in (
            SOURCE_TYPE_WORKFLOW, SOURCE_TYPE_TEMPLATE,
        ):
            _, user_rows, group_ids = _rebuild_workflow_attachment(
                att, workflow,
                UserObjectPermission, GroupObjectPermission,
                att_ct, att_perm, wf_ct, view_perm,
                TaskPerformer, TemplateOwner, Task,
            )
        else:
            continue

        for uid, source_type, source_id in user_rows:
            user_batch.append(UserObjectPermission(
                user_id=uid,
                permission=att_perm,
                content_type=att_ct,
                object_pk=obj_pk,
                source_type=source_type,
                source_id=int(source_id),
            ))

        for gid in group_ids:
            group_batch.append(GroupObjectPermission(
                group_id=gid,
                permission=att_perm,
                content_type=att_ct,
                object_pk=obj_pk,
            ))

        processed += 1

        if len(user_batch) >= BATCH_SIZE:
            UserObjectPermission.objects.bulk_create(
                user_batch, ignore_conflicts=True,
            )
            user_batch = []
        if len(group_batch) >= BATCH_SIZE:
            GroupObjectPermission.objects.bulk_create(
                group_batch, ignore_conflicts=True,
            )
            group_batch = []

    if user_batch:
        UserObjectPermission.objects.bulk_create(
            user_batch, ignore_conflicts=True,
        )
    if group_batch:
        GroupObjectPermission.objects.bulk_create(
            group_batch, ignore_conflicts=True,
        )


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0255_migrate_workflow_acl_to_guardian'),
        ('storage', '0001_initial'),
        ('permissions', '0002_user_object_permission'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
