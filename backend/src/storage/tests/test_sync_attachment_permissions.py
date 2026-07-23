import pytest
from unittest.mock import call
from django.contrib.contenttypes.models import ContentType

from src.permissions.enums import PermissionSource
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.events import WorkflowEventService
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tasks.update_workflow import update_workflow_owners
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_attachment,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.permissions.models import UserObjectPermission
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.tasks import sync_workflow_attachment_permissions


@pytest.mark.django_db
def test_sync_wf_att_perms__basic__reassigns_permissions():
    """When called, reassigns access_attachment for all
    restricted attachments in the workflow."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    attachment = create_test_attachment(
        account=account,
        file_id='test_sync.pdf',
        task=task,
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )

    # Assign initial permissions
    service = AttachmentService()
    service.assign_permissions(attachment)

    # Verify user has access
    assert service.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=attachment.file_id,
    )

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert service.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=attachment.file_id,
    )


@pytest.mark.django_db
def test_sync_wf_att_perms__task_only_no_workflow_fk__reassigns():
    """Task description files often have workflow_id=NULL.

    sync_workflow_attachment_permissions must still find them
    via task__workflow and reassign ACL (e.g. after mention).
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    mentioned = create_test_not_admin(
        account=account,
        email='mentioned@test.test',
    )
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    attachment = create_test_attachment(
        account=account,
        file_id='task_desc_only.pdf',
        task=task,
        workflow=None,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )
    service = AttachmentService()
    service.assign_permissions(attachment)
    WorkflowPermissionService(workflow).grant_view(
        user=mentioned,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert service.check_user_permission(
        user_id=mentioned.id,
        account_id=mentioned.account_id,
        file_id=attachment.file_id,
    )


@pytest.mark.django_db
def test_sync_wf_att_perms__event_only_no_workflow_fk__ok():

    """Event attachments with workflow_id=NULL must still sync
    via event__workflow."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    viewer = create_test_not_admin(
        account=account,
        email='ev_viewer@test.test',
    )
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    event = WorkflowEventService.task_started_event(
        task=task,
        after_create_actions=False,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='event_only.pdf',
        event=event,
        workflow=None,
        task=None,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.WORKFLOW,
    )
    service = AttachmentService()
    service.assign_permissions(attachment)

    WorkflowPermissionService(workflow).grant_view(
        user=viewer,
        source_type=PermissionSource.MENTION,
        source_id=1,
    )

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert service.check_user_permission(
        user_id=viewer.id,
        account_id=viewer.account_id,
        file_id=attachment.file_id,
    )


@pytest.mark.django_db
def test_sync_wf_att_perms__removed_performer__loses_access():
    """When a performer is removed from a task and
    sync_performer_sources() recalculates workflow permissions,
    the Celery task also revokes access_attachment on related files."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    performer = create_test_not_admin(
        account=account,
        email='performer@test.test',
    )
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)

    # Add performer to task
    TaskPerformer.objects.create(
        task=task,
        user=performer,
        type=PerformerType.USER,
    )

    # Grant view_workflow to performer
    WorkflowPermissionService(workflow).grant_view(
        user=performer,
        source_type=PermissionSource.PERFORMER,
        source_id=task.id,
    )

    # Create attachment and assign permissions
    attachment = create_test_attachment(
        account=account,
        file_id='secret_doc.pdf',
        task=task,
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )
    service = AttachmentService()
    service.assign_permissions(attachment)

    # Verify performer has access
    assert service.check_user_permission(
        user_id=performer.id,
        account_id=performer.account_id,
        file_id=attachment.file_id,
    )

    # Remove performer from task
    TaskPerformer.objects.filter(
        task=task,
        user=performer,
    ).delete()

    # Recalculate workflow viewers
    WorkflowPermissionService(workflow).sync_performer_sources()

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert not service.check_user_permission(
        user_id=performer.id,
        account_id=performer.account_id,
        file_id=attachment.file_id,
    )


@pytest.mark.django_db
def test_sync_wf_att_perms__nonexistent_wf__skips_silently():
    """When workflow_id does not exist, the task does not raise."""

    # arrange
    nonexistent_id = 999999

    # act
    sync_workflow_attachment_permissions(nonexistent_id)

    # assert — no exception raised


@pytest.mark.django_db
def test_sync_wf_att_perms__soft_deleted_wf__skips_silently():
    """When workflow exists but is_deleted=True, the task skips."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    workflow.is_deleted = True
    workflow.save(update_fields=['is_deleted'])
    att_ct = ContentType.objects.get_for_model(Attachment)
    perm_count_before = UserObjectPermission.objects.filter(
        content_type=att_ct,
    ).count()

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    perm_count_after = UserObjectPermission.objects.filter(
        content_type=att_ct,
    ).count()
    assert perm_count_after == perm_count_before


@pytest.mark.django_db
def test_sync_wf_att_perms__no_restricted_atts__noop():
    """When workflow has no restricted attachments, runs ok."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert — no exception raised


@pytest.mark.django_db
def test_sync_wf_att_perms__public_att__ignored():
    """Public attachments are not processed by sync task."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    create_test_attachment(
        account=account,
        file_id='public_file.pdf',
        task=task,
        workflow=workflow,
        access_type=AccessType.PUBLIC,
        source_type=SourceType.TASK,
    )
    restricted_att = create_test_attachment(
        account=account,
        file_id='restricted_file.pdf',
        task=task,
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )
    service = AttachmentService()
    service.assign_permissions(restricted_att)

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert service.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=restricted_att.file_id,
    )


@pytest.mark.django_db
def test_sync_wf_att_perms__wf_level_att__reassigned():
    """Workflow-level attachments (not task-level) are also
    reassigned by the sync task."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    attachment = create_test_attachment(
        account=account,
        file_id='workflow_doc.pdf',
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.WORKFLOW,
    )
    service = AttachmentService()
    service.assign_permissions(attachment)

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert service.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=attachment.file_id,
    )


@pytest.mark.django_db
def test_sync_wf_att_perms__multiple_atts__all_reassigned():
    """Multiple attachments across tasks are all reassigned."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    att_1 = create_test_attachment(
        account=account,
        file_id='file1.pdf',
        task=task_1,
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )
    att_2 = create_test_attachment(
        account=account,
        file_id='file2.pdf',
        task=task_2,
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )
    service = AttachmentService()
    service.assign_permissions(att_1)
    service.assign_permissions(att_2)

    # act
    sync_workflow_attachment_permissions(workflow.id)

    # assert
    assert service.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=att_1.file_id,
    )
    assert service.check_user_permission(
        user_id=user.id,
        account_id=user.account_id,
        file_id=att_2.file_id,
    )


@pytest.mark.django_db
def test_update_wf_owners__owner_change__att_perms_synced(
    mocker,
):
    """When template owners change, attachment permissions
    are synced via the Celery task."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )

    sync_wf_att_perms_mock = mocker.patch(
        'src.processes.tasks.update_workflow.'
        'schedule_sync_workflow_attachment_permissions',
    )

    # act
    update_workflow_owners([template.id])

    # assert
    sync_wf_att_perms_mock.assert_called_once_with(
        workflow.id,
    )


@pytest.mark.django_db
def test_update_wf_owners__multiple_wfs__each_synced(
    mocker,
):
    """When template has multiple workflows, each gets synced."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow_1 = create_test_workflow(
        user=user,
        template=template,
    )
    workflow_2 = create_test_workflow(
        user=user,
        template=template,
    )

    sync_wf_att_perms_mock = mocker.patch(
        'src.processes.tasks.update_workflow.'
        'schedule_sync_workflow_attachment_permissions',
    )

    # act
    update_workflow_owners([template.id])

    # assert
    assert sync_wf_att_perms_mock.call_count == 2
    sync_wf_att_perms_mock.assert_has_calls(
        [
            call(workflow_1.id),
            call(workflow_2.id),
        ],
        any_order=True,
    )


@pytest.mark.django_db
def test_delete_orphaned_perfs__orphan__triggers_att_sync(
    mocker,
):
    """When orphaned performers are deleted and
    sync_performer_sources is called, attachment sync is also
    triggered via Celery."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    extra_performer = create_test_not_admin(
        account=account,
        email='extra@test.test',
    )
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.get(number=1)

    sync_wf_att_perms_mock = mocker.patch(
        'src.storage.tasks.'
        'schedule_sync_workflow_attachment_permissions',
    )

    # Create a performer without raw performer (orphan)
    TaskPerformer.objects.create(
        task=task,
        user=extra_performer,
        type=PerformerType.USER,
    )

    # act
    task._delete_orphaned_performers()

    # assert
    sync_wf_att_perms_mock.assert_called_once_with(
        workflow.id,
    )
