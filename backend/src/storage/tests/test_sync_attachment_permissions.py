import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tasks.update_workflow import update_workflow_owners
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_attachment,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.services.attachments import AttachmentService
from src.storage.tasks import sync_workflow_attachment_permissions

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestSyncWorkflowAttachmentPermissions:
    """Tests for the sync_workflow_attachment_permissions Celery task."""

    def test__basic__reassigns_permissions(self):
        """When called, reassigns access_attachment for all
        restricted attachments in the workflow."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
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
        service = AttachmentService(user=user)
        service.assign_permissions(attachment)

        # Verify user has access
        assert service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # act — run the Celery task synchronously
        sync_workflow_attachment_permissions(workflow.id)

        # assert — permissions still valid after sync
        assert service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

    def test__removed_performer__loses_attachment_access(self):
        """When a performer is removed from a task and set_viewers()
        recalculates workflow permissions, the Celery task also
        revokes access_attachment on related files."""

        # arrange
        account = create_test_account()
        owner = create_test_user(account=account)
        performer = create_test_user(
            account=account,
            email='performer@test.test',
            is_account_owner=False,
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
        WorkflowPermissionService.grant_view(performer, workflow)

        # Create attachment and assign permissions
        attachment = create_test_attachment(
            account=account,
            file_id='secret_doc.pdf',
            task=task,
            workflow=workflow,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
        )
        service = AttachmentService(user=owner)
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

        # Recalculate workflow viewers (simulates what set_viewers does)
        WorkflowPermissionService.set_viewers(workflow)

        # act — run the Celery task synchronously
        sync_workflow_attachment_permissions(workflow.id)

        # assert — performer no longer has access to attachment
        assert not service.check_user_permission(
            user_id=performer.id,
            account_id=performer.account_id,
            file_id=attachment.file_id,
        )

    def test__deleted_workflow__skips_silently(self):
        """When workflow is deleted, the task does not raise."""

        # act/assert — should not raise
        sync_workflow_attachment_permissions(999999)

    def test__no_restricted_attachments__noop(self):
        """When workflow has no restricted attachments, runs without error."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=user,
            template=template,
        )

        # act/assert — no attachments, should run fine
        sync_workflow_attachment_permissions(workflow.id)

    def test__workflow_level_attachment__reassigned(self):
        """Workflow-level attachments (not task-level) are also
        reassigned by the sync task."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
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
        service = AttachmentService(user=user)
        service.assign_permissions(attachment)
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

    def test__multiple_attachments__all_reassigned(self):
        """Multiple attachments across tasks are all reassigned."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
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

        service = AttachmentService(user=user)
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


class TestUpdateWorkflowOwnersSyncsAttachments:
    """Verifies that update_workflow_owners triggers attachment
    permission sync for affected workflows."""

    def test__owner_change__attachment_permissions_updated(self, mocker):
        """When template owners change, attachment permissions
        are synced via the Celery task."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        workflow = create_test_workflow(
            user=user,
            template=template,
        )

        mock_sync = mocker.patch(
            'src.processes.tasks.update_workflow'
            '.sync_workflow_attachment_permissions',
        )

        # act
        update_workflow_owners([template.id])

        # assert — sync task was called for this workflow
        mock_sync.delay.assert_called_with(workflow.id)

    def test__multiple_workflows__each_synced(self, mocker):
        """When template has multiple workflows, each gets synced."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
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

        mock_sync = mocker.patch(
            'src.processes.tasks.update_workflow'
            '.sync_workflow_attachment_permissions',
        )

        # act
        update_workflow_owners([template.id])

        # assert
        mock_sync.delay.assert_any_call(workflow_1.id)
        mock_sync.delay.assert_any_call(workflow_2.id)


class TestOrphanedPerformersSyncsAttachments:
    """Verifies that _delete_orphaned_performers triggers
    attachment permission sync."""

    def test__orphan_cleanup__triggers_attachment_sync(self, mocker):
        """When orphaned performers are deleted and set_viewers is called,
        attachment sync is also triggered via Celery."""

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        extra_performer = create_test_user(
            account=account,
            email='extra@test.test',
            is_account_owner=False,
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

        mock_sync = mocker.patch(
            'src.storage.tasks.sync_workflow_attachment_permissions',
        )

        # Create a performer without raw performer (orphan)
        TaskPerformer.objects.create(
            task=task,
            user=extra_performer,
            type=PerformerType.USER,
        )

        # act — trigger orphan cleanup
        task._delete_orphaned_performers()

        # assert
        mock_sync.delay.assert_called_once_with(workflow.id)
