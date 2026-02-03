"""
E2E tests for comment attachments workflow.
Tests full workflow without mocks - real database operations.
"""
import pytest

from src.processes.models.workflows.event import WorkflowEvent
from src.processes.enums import WorkflowEventType
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_group,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.utils import _refresh_workflow_event_attachments

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def file_domain_comment_e2e(settings):
    settings.FILE_DOMAIN = 'files.example.com'


class TestCommentAttachmentsE2E:
    """
    End-to-end tests for comment attachments.
    No mocks - testing real integration.
    """

    def test_task_comment_with_attachment__all_participants_access__ok(
        self,
    ):
        """
        Scenario: User adds comment with file to task
        Expected: All task participants have access to attachment
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
        task.taskperformer_set.create(user=performer2)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=performer1,
            type=WorkflowEventType.COMMENT,
            text=(
                'Please review this file: '
                'https://files.example.com/files/task_comment_e2e_123'
            ),
        )

        # act
        new_file_ids = _refresh_workflow_event_attachments(
            comment_event,
            performer1,
        )

        # assert
        assert 'task_comment_e2e_123' in new_file_ids
        attachment = Attachment.objects.get(
            file_id='task_comment_e2e_123',
        )
        assert attachment.task == task
        assert attachment.source_type == SourceType.TASK
        assert attachment.access_type == AccessType.RESTRICTED
        svc_o = AttachmentService(user=owner)
        svc_p1 = AttachmentService(user=performer1)
        svc_p2 = AttachmentService(user=performer2)
        assert svc_o.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc_p1.check_user_permission(
            user_id=performer1.id,
            account_id=performer1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_p2.check_user_permission(
            user_id=performer2.id,
            account_id=performer2.account_id,
            file_id=attachment.file_id,
        )

    def test_workflow_comment_with_attachment__members_access__ok(
        self,
    ):
        """
        Scenario: User adds comment with file to workflow
        Expected: All workflow members have access to attachment
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
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=None,  # Workflow-level comment
            account=owner.account,
            user=member1,
            type=WorkflowEventType.COMMENT,
            text=(
                'Workflow file: '
                'https://files.example.com/files/workflow_comment_e2e_456'
            ),
        )

        # act
        new_file_ids = _refresh_workflow_event_attachments(
            comment_event,
            member1,
        )

        # assert
        assert 'workflow_comment_e2e_456' in new_file_ids
        attachment = Attachment.objects.get(
            file_id='workflow_comment_e2e_456',
        )
        assert attachment.workflow == workflow
        assert attachment.source_type == SourceType.WORKFLOW
        assert attachment.access_type == AccessType.RESTRICTED
        svc_o = AttachmentService(user=owner)
        svc_m1 = AttachmentService(user=member1)
        svc_m2 = AttachmentService(user=member2)
        assert svc_o.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc_m1.check_user_permission(
            user_id=member1.id,
            account_id=member1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_m2.check_user_permission(
            user_id=member2.id,
            account_id=member2.account_id,
            file_id=attachment.file_id,
        )

    def test_comment_with_group_performers__all_group_users_access__ok(
        self,
    ):
        """
        Scenario: Comment on task with group performers
        Expected: All users in performer groups have access
        """
        # arrange
        owner = create_test_admin()
        group_user1 = create_test_user(
            account=owner.account,
            email='group_user1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='group_user2@test.pneumatic.app',
        )
        individual_user = create_test_user(
            account=owner.account,
            email='individual@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Comment Test Group',
            users=[group_user1, group_user2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        task.taskperformer_set.create(user=individual_user)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=group_user1,
            type=WorkflowEventType.COMMENT,
            text=(
                'Group file: '
                'https://files.example.com/files/group_comment_e2e_789'
            ),
        )

        # act
        new_file_ids = _refresh_workflow_event_attachments(
            comment_event,
            group_user1,
        )

        # assert
        assert 'group_comment_e2e_789' in new_file_ids
        attachment = Attachment.objects.get(
            file_id='group_comment_e2e_789',
        )
        svc_gu1 = AttachmentService(user=group_user1)
        svc_gu2 = AttachmentService(user=group_user2)
        svc_ind = AttachmentService(user=individual_user)
        assert svc_gu1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_gu2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )
        assert svc_ind.check_user_permission(
            user_id=individual_user.id,
            account_id=individual_user.account_id,
            file_id=attachment.file_id,
        )

    def test_comment_multiple_files__all_created_with_permissions__ok(
        self,
    ):
        """
        Scenario: Comment contains multiple file links
        Expected: All attachments created with correct permissions
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=performer,
            type=WorkflowEventType.COMMENT,
            text=(
                'Multiple files: '
                'https://files.example.com/files/multi_comment_1_e2e and '
                'https://files.example.com/files/multi_comment_2_e2e'
            ),
        )

        # act
        new_file_ids = _refresh_workflow_event_attachments(
            comment_event,
            performer,
        )

        # assert
        assert len(new_file_ids) == 2
        assert 'multi_comment_1_e2e' in new_file_ids
        assert 'multi_comment_2_e2e' in new_file_ids
        svc = AttachmentService(user=performer)
        for file_id in new_file_ids:
            attachment = Attachment.objects.get(file_id=file_id)
            assert svc.check_user_permission(
                user_id=performer.id,
                account_id=performer.account_id,
                file_id=attachment.file_id,
            )

    def test_non_participant_comment_attachment__no_access__ok(
        self,
    ):
        """
        Scenario: Non-participant tries to access comment attachment
        Expected: No access to attachment
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(
            account=owner.account,
            email='performer@test.pneumatic.app',
        )
        other_user = create_test_user(
            account=owner.account,
            email='other@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=performer,
            type=WorkflowEventType.COMMENT,
            text=(
                'Private file: '
                'https://files.example.com/files/private_comment_e2e'
            ),
        )

        # act
        _refresh_workflow_event_attachments(comment_event, performer)

        # assert
        attachment = Attachment.objects.get(
            file_id='private_comment_e2e',
        )
        svc = AttachmentService(user=other_user)
        assert not svc.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id=attachment.file_id,
        )

    def test_comment_attachment_permissions_inheritance__ok(self):
        """
        Scenario: Comment attachment inherits permissions from task/workflow
        Expected: Same users who can access task can access comment files
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        member = create_test_user(email='tt@gmail.com', account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=performer,
            type=WorkflowEventType.COMMENT,
            text=(
                'Inherited file: '
                'https://files.example.com/files/inherited_comment_e2e'
            ),
        )

        # act
        _refresh_workflow_event_attachments(comment_event, performer)

        # assert
        attachment = Attachment.objects.get(
            file_id='inherited_comment_e2e',
        )
        svc_o = AttachmentService(user=owner)
        svc_p = AttachmentService(user=performer)
        svc_m = AttachmentService(user=member)
        # All task/workflow participants should have access
        assert svc_o.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc_p.check_user_permission(
            user_id=performer.id,
            account_id=performer.account_id,
            file_id=attachment.file_id,
        )
        assert svc_m.check_user_permission(
            user_id=member.id,
            account_id=member.account_id,
            file_id=attachment.file_id,
        )

    def test_update_comment_with_new_file__new_attachment_created__ok(
        self,
    ):
        """
        Scenario: Update comment to add new file
        Expected: New attachment created with permissions
        """
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        comment_event = WorkflowEvent.objects.create(
            workflow=workflow,
            task=task,
            account=owner.account,
            user=performer,
            type=WorkflowEventType.COMMENT,
            text='Initial comment without files',
        )
        _refresh_workflow_event_attachments(comment_event, performer)

        # act
        comment_event.text = (
            'Updated comment: '
            'https://files.example.com/files/updated_comment_e2e'
        )
        comment_event.save()
        new_file_ids = _refresh_workflow_event_attachments(
            comment_event,
            performer,
        )

        # assert
        assert 'updated_comment_e2e' in new_file_ids
        assert Attachment.objects.filter(
            file_id='updated_comment_e2e',
            task=task,
        ).exists()
