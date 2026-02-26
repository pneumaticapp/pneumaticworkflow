"""
E2E tests for task attachments workflow.
Tests full workflow without mocks - real database operations.
"""
import pytest

from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.utils import _refresh_workflow_event_attachments
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.utils import refresh_attachments

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def file_base_url_task_e2e(settings):
    settings.FILE_SERVICE_URL = 'https://files.example.com'
    settings.FILE_DOMAIN = 'files.example.com'


class TestTaskAttachmentsE2E:
    """
    End-to-end tests for task attachments.
    No mocks - testing real integration.
    """

    def test_create_task_with_attachment__full_workflow__ok(self):
        """
        Scenario: Create task with file in description
        Expected: Attachment created with correct permissions
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        task.description = (
            'Please check file: '
            '[file](https://files.example.com/task_file_e2e_123)'
        )
        task.save()

        # act
        new_file_ids = refresh_attachments(source=task, user=owner)

        # assert
        assert 'task_file_e2e_123' in new_file_ids
        attachment = Attachment.objects.get(file_id='task_file_e2e_123')
        assert attachment.task == task
        assert attachment.source_type == SourceType.TASK
        assert attachment.access_type == AccessType.RESTRICTED
        svc_p = AttachmentService(user=performer)
        svc_o = AttachmentService(user=owner)
        assert svc_p.check_user_permission(
            user_id=performer.id,
            account_id=performer.account_id,
            file_id=attachment.file_id,
        )
        assert svc_o.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_update_task_description__add_file__ok(self):
        """
        Scenario: Update task description to add new file
        Expected: New attachment created with permissions
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.description = 'Initial description'
        task.save()
        refresh_attachments(source=task, user=owner)

        # act
        task.description = (
            'Updated with file: '
            '[file](https://files.example.com/new_file_e2e_456)'
        )
        task.save()
        new_file_ids = refresh_attachments(source=task, user=owner)

        # assert
        assert 'new_file_e2e_456' in new_file_ids
        assert Attachment.objects.filter(
            file_id='new_file_e2e_456',
            task=task,
        ).exists()

    def test_update_task_description__remove_file__deleted(self):
        """
        Scenario: Remove file link from task description
        Expected: Attachment deleted
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.description = (
            'File: [f](https://files.example.com/remove_file_e2e_789)'
        )
        task.save()
        refresh_attachments(source=task, user=owner)
        assert Attachment.objects.filter(
            file_id='remove_file_e2e_789',
        ).exists()

        # act
        task.description = 'No files anymore'
        task.save()
        refresh_attachments(source=task, user=owner)

        # assert
        assert not Attachment.objects.filter(
            file_id='remove_file_e2e_789',
        ).exists()

    def test_refresh_task_description__comment_attachments_preserved__ok(
        self,
    ):
        """
        Scenario: Task has description file + comment with file.
        User changes task description (refresh_attachments runs).
        Expected: Only description (scope) attachments updated;
        comment (event) attachments must not be deleted.
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        task.description = (
            'Description file: '
            '[f](https://files.example.com/task_desc_scope_e2e)'
        )
        task.save()
        refresh_attachments(source=task, user=owner)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=performer,
            type=WorkflowEventType.COMMENT,
            text=(
                'Comment file: '
                '[f](https://files.example.com/task_comment_event_e2e)'
            ),
        )
        _refresh_workflow_event_attachments(comment_event, performer)
        assert Attachment.objects.filter(
            file_id='task_desc_scope_e2e', event__isnull=True,
        ).exists()
        assert Attachment.objects.filter(
            file_id='task_comment_event_e2e', event=comment_event,
        ).exists()

        # act: change task description (remove scope file), refresh task
        task.description = 'No files in description'
        task.save()
        refresh_attachments(source=task, user=owner)

        # assert: scope attachment removed, comment attachment preserved
        assert not Attachment.objects.filter(
            file_id='task_desc_scope_e2e',
        ).exists()
        assert Attachment.objects.filter(
            file_id='task_comment_event_e2e',
            event=comment_event,
        ).exists()

    def test_add_performer__gets_access__ok(self):
        """
        Scenario: Add new performer to task with existing attachment
        Expected: New performer gets access to attachment
        """
        # arrange
        owner = create_test_admin()
        performer1 = create_test_user(
            account=owner.account,
            email='performer1@test.pneumatic.app',
        )
        performer2 = create_test_user(
            account=owner.account,
            email='performer2@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer1)
        task.description = (
            'File: [f](https://files.example.com/performer_file_e2e)'
        )
        task.save()
        refresh_attachments(source=task, user=owner)
        attachment = Attachment.objects.get(
            file_id='performer_file_e2e',
        )
        svc1 = AttachmentService(user=performer1)
        svc2 = AttachmentService(user=performer2)
        assert svc1.check_user_permission(
            user_id=performer1.id,
            account_id=performer1.account_id,
            file_id=attachment.file_id,
        )
        assert not svc2.check_user_permission(
            user_id=performer2.id,
            account_id=performer2.account_id,
            file_id=attachment.file_id,
        )

        # act
        task.taskperformer_set.create(user=performer2)
        service = AttachmentService(user=owner)
        service.instance = attachment
        service._create_related()

        # assert
        svc2 = AttachmentService(user=performer2)
        assert svc2.check_user_permission(
            user_id=performer2.id,
            account_id=performer2.account_id,
            file_id=attachment.file_id,
        )

    def test_multiple_files_in_description__all_created__ok(self):
        """
        Scenario: Task description contains multiple file links
        Expected: All attachments created with permissions
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(
            account=owner.account,
            email='performer_multi@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        task.description = (
            'Files: '
            '[a](https://files.example.com/multi_file_1_e2e) '
            '[b](https://files.example.com/multi_file_2_e2e) '
            '[c](https://files.example.com/multi_file_3_e2e)'
        )
        task.save()

        # act
        new_file_ids = refresh_attachments(source=task, user=owner)

        # assert
        assert len(new_file_ids) == 3
        assert 'multi_file_1_e2e' in new_file_ids
        assert 'multi_file_2_e2e' in new_file_ids
        assert 'multi_file_3_e2e' in new_file_ids
        svc = AttachmentService(user=performer)
        for file_id in new_file_ids:
            attachment = Attachment.objects.get(file_id=file_id)
            assert svc.check_user_permission(
                user_id=performer.id,
                account_id=performer.account_id,
                file_id=attachment.file_id,
            )

    def test_check_permission_via_service__ok(self):
        """
        Scenario: Check permission using service method
        Expected: Correct permission check result
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(
            account=owner.account,
            email='performer_check@test.pneumatic.app',
        )
        other_user = create_test_user(
            account=owner.account,
            email='other_check@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        task.description = (
            'File: [f](https://files.example.com/check_perm_e2e)'
        )
        task.save()
        refresh_attachments(source=task, user=owner)
        service = AttachmentService(user=performer)

        # act
        has_permission = service.check_user_permission(
            user_id=performer.id,
            account_id=performer.account_id,
            file_id='check_perm_e2e',
        )
        no_permission = service.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id='check_perm_e2e',
        )

        # assert
        assert has_permission is True
        assert no_permission is False

    def test_task_with_workflow_members__all_have_access__ok(self):
        """
        Scenario: Task in workflow with members
        Expected: All workflow members have access to task attachment
        """
        # arrange
        owner = create_test_admin()
        member1 = create_test_user(
            account=owner.account,
            email='member1@test.pneumatic.app',
        )
        member2 = create_test_user(
            account=owner.account,
            email='member2@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member1, member2)
        task = workflow.tasks.first()
        task.description = (
            'File: [f](https://files.example.com/members_file_e2e)'
        )
        task.save()

        # act
        refresh_attachments(source=task, user=owner)

        # assert
        attachment = Attachment.objects.get(file_id='members_file_e2e')
        svc_o = AttachmentService(user=owner)
        svc1 = AttachmentService(user=member1)
        svc2 = AttachmentService(user=member2)
        assert svc_o.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc1.check_user_permission(
            user_id=member1.id,
            account_id=member1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=member2.id,
            account_id=member2.account_id,
            file_id=attachment.file_id,
        )

    def test_replace_file_in_description__old_deleted_new_created__ok(
        self,
    ):
        """
        Scenario: Replace file link in task description
        Expected: Old attachment deleted, new created
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.description = (
            'File: [f](https://files.example.com/old_file_e2e)'
        )
        task.save()
        refresh_attachments(source=task, user=owner)
        assert Attachment.objects.filter(
            file_id='old_file_e2e',
        ).exists()

        # act
        task.description = (
            'File: [f](https://files.example.com/new_file_e2e)'
        )
        task.save()
        refresh_attachments(source=task, user=owner)

        # assert
        assert not Attachment.objects.filter(
            file_id='old_file_e2e',
        ).exists()
        assert Attachment.objects.filter(
            file_id='new_file_e2e',
        ).exists()

    def test_bulk_create_with_permissions__ok(self):
        """
        Scenario: Bulk create attachments for task
        Expected: All attachments created with correct permissions
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        service = AttachmentService(user=owner)
        file_ids = [
            'bulk_e2e_1',
            'bulk_e2e_2',
            'bulk_e2e_3',
        ]

        # act
        attachments = service.bulk_create(
            file_ids=file_ids,
            source=task,
        )

        # assert
        assert len(attachments) == 3
        svc_p = AttachmentService(user=performer)
        svc_o = AttachmentService(user=owner)
        for attachment in attachments:
            assert attachment.task == task
            assert svc_p.check_user_permission(
                user_id=performer.id,
                account_id=performer.account_id,
                file_id=attachment.file_id,
            )
            assert svc_o.check_user_permission(
                user_id=owner.id,
                account_id=owner.account_id,
                file_id=attachment.file_id,
            )
