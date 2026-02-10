"""
E2E tests for workflow attachments.
Tests full workflow without mocks - real database operations.
"""
import pytest

from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.utils import refresh_attachments

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def file_domain_workflow_e2e(settings):
    settings.FILE_DOMAIN = 'files.example.com'


class TestWorkflowAttachmentsE2E:
    """
    End-to-end tests for workflow attachments.
    No mocks - testing real integration.
    """

    def test_create_workflow_with_attachment__full_workflow__ok(
        self,
    ):
        """
        Scenario: Create workflow with file in description
        Expected: Attachment created with correct permissions
        """
        # arrange
        owner = create_test_admin()
        member = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member)
        workflow.description = (
            'Workflow file: '
            'https://files.example.com/workflow_e2e_123'
        )
        workflow.save()

        # act
        new_file_ids = refresh_attachments(source=workflow, user=owner)

        # assert
        assert 'workflow_e2e_123' in new_file_ids
        attachment = Attachment.objects.get(file_id='workflow_e2e_123')
        assert attachment.workflow == workflow
        assert attachment.source_type == SourceType.WORKFLOW
        assert attachment.access_type == AccessType.RESTRICTED
        svc_o = AttachmentService(user=owner)
        svc_m = AttachmentService(user=member)
        assert svc_o.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc_m.check_user_permission(
            user_id=member.id,
            account_id=member.account_id,
            file_id=attachment.file_id,
        )

    def test_workflow_with_task_performers__all_have_access__ok(
        self,
    ):
        """
        Scenario: Workflow with task performers
        Expected: All task performers have access to workflow attachment
        """
        # arrange
        owner = create_test_admin()
        performer1 = create_test_user(
            account=owner.account,
            email='wf_performer1@test.pneumatic.app',
        )
        performer2 = create_test_user(
            account=owner.account,
            email='wf_performer2@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=2)
        task1 = workflow.tasks.first()
        task2 = workflow.tasks.last()
        task1.taskperformer_set.create(user=performer1)
        task2.taskperformer_set.create(user=performer2)
        workflow.description = (
            'File: https://files.example.com/wf_performers_e2e'
        )
        workflow.save()

        # act
        refresh_attachments(source=workflow, user=owner)

        # assert
        attachment = Attachment.objects.get(
            file_id='wf_performers_e2e',
        )
        svc1 = AttachmentService(user=performer1)
        svc2 = AttachmentService(user=performer2)
        assert svc1.check_user_permission(
            user_id=performer1.id,
            account_id=performer1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=performer2.id,
            account_id=performer2.account_id,
            file_id=attachment.file_id,
        )

    def test_update_workflow_description__add_file__ok(self):
        """
        Scenario: Update workflow description to add new file
        Expected: New attachment created with permissions
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.description = 'Initial workflow description'
        workflow.save()
        refresh_attachments(source=workflow, user=owner)

        # act
        workflow.description = (
            'Updated: https://files.example.com/wf_new_e2e'
        )
        workflow.save()
        new_file_ids = refresh_attachments(source=workflow, user=owner)

        # assert
        assert 'wf_new_e2e' in new_file_ids
        assert Attachment.objects.filter(
            file_id='wf_new_e2e',
            workflow=workflow,
        ).exists()

    def test_update_workflow_description__remove_file__deleted(
        self,
    ):
        """
        Scenario: Remove file link from workflow description
        Expected: Attachment deleted
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.description = (
            'File: https://files.example.com/wf_remove_e2e'
        )
        workflow.save()
        refresh_attachments(source=workflow, user=owner)
        assert Attachment.objects.filter(
            file_id='wf_remove_e2e',
        ).exists()

        # act
        workflow.description = 'No files'
        workflow.save()
        refresh_attachments(source=workflow, user=owner)

        # assert
        assert not Attachment.objects.filter(
            file_id='wf_remove_e2e',
        ).exists()

    def test_add_workflow_member__gets_access__ok(self):
        """
        Scenario: Add new member to workflow with existing attachment
        Expected: New member gets access to attachment
        """
        # arrange
        owner = create_test_admin()
        member1 = create_test_user(
            account=owner.account,
            email='wf_member1@test.pneumatic.app',
        )
        member2 = create_test_user(
            account=owner.account,
            email='wf_member2@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member1)
        workflow.description = (
            'File: https://files.example.com/wf_member_e2e'
        )
        workflow.save()
        refresh_attachments(source=workflow, user=owner)
        attachment = Attachment.objects.get(file_id='wf_member_e2e')
        svc1 = AttachmentService(user=member1)
        svc2 = AttachmentService(user=member2)
        assert svc1.check_user_permission(
            user_id=member1.id,
            account_id=member1.account_id,
            file_id=attachment.file_id,
        )
        assert not svc2.check_user_permission(
            user_id=member2.id,
            account_id=member2.account_id,
            file_id=attachment.file_id,
        )

        # act
        workflow.members.add(member2)
        refresh_attachments(source=workflow, user=owner)

        # assert
        attachment.refresh_from_db()
        assert svc2.check_user_permission(
            user_id=member2.id,
            account_id=member2.account_id,
            file_id=attachment.file_id,
        )

    def test_workflow_multiple_files__all_created__ok(self):
        """
        Scenario: Workflow description contains multiple file links
        Expected: All attachments created with permissions
        """
        # arrange
        owner = create_test_admin()
        member = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member)
        workflow.description = (
            'Files: '
            'https://files.example.com/wf_multi_1_e2e and '
            'https://files.example.com/wf_multi_2_e2e'
        )
        workflow.save()

        # act
        new_file_ids = refresh_attachments(source=workflow, user=owner)

        # assert
        assert len(new_file_ids) == 2
        svc = AttachmentService(user=member)
        for file_id in new_file_ids:
            attachment = Attachment.objects.get(file_id=file_id)
            assert svc.check_user_permission(
                user_id=member.id,
                account_id=member.account_id,
                file_id=attachment.file_id,
            )

    def test_workflow_owner_always_has_access__ok(self):
        """
        Scenario: Workflow owner
        Expected: Owner always has access to workflow attachments
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.description = (
            'File: https://files.example.com/wf_owner_e2e'
        )
        workflow.save()

        # act
        refresh_attachments(source=workflow, user=owner)

        # assert
        attachment = Attachment.objects.get(file_id='wf_owner_e2e')
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_non_participant_no_access__ok(self):
        """
        Scenario: User not participating in workflow
        Expected: No access to workflow attachments
        """
        # arrange
        owner = create_test_admin()
        other_user = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.description = (
            'File: https://files.example.com/wf_no_access_e2e'
        )
        workflow.save()

        # act
        refresh_attachments(source=workflow, user=owner)

        # assert
        attachment = Attachment.objects.get(
            file_id='wf_no_access_e2e',
        )
        svc = AttachmentService(user=other_user)
        assert not svc.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id=attachment.file_id,
        )

    def test_workflow_with_owners__all_have_access__ok(self):
        """
        Scenario: Workflow with multiple owners
        Expected: All owners have access to attachments
        """
        # arrange
        owner1 = create_test_admin()
        owner2 = create_test_user(account=owner1.account, is_admin=True)
        workflow = create_test_workflow(user=owner1, tasks_count=1)
        workflow.owners.add(owner1, owner2)
        workflow.description = (
            'File: https://files.example.com/wf_owners_e2e'
        )
        workflow.save()

        # act
        refresh_attachments(source=workflow, user=owner1)

        # assert
        attachment = Attachment.objects.get(file_id='wf_owners_e2e')
        svc1 = AttachmentService(user=owner1)
        svc2 = AttachmentService(user=owner2)
        assert svc1.check_user_permission(
            user_id=owner1.id,
            account_id=owner1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=owner2.id,
            account_id=owner2.account_id,
            file_id=attachment.file_id,
        )

    def test_replace_file_in_workflow__old_deleted_new_created__ok(
        self,
    ):
        """
        Scenario: Replace file link in workflow description
        Expected: Old attachment deleted, new created
        """
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.description = (
            'File: https://files.example.com/wf_old_e2e'
        )
        workflow.save()
        refresh_attachments(source=workflow, user=owner)
        assert Attachment.objects.filter(file_id='wf_old_e2e').exists()

        # act
        workflow.description = (
            'File: https://files.example.com/wf_new_replace_e2e'
        )
        workflow.save()
        refresh_attachments(source=workflow, user=owner)

        # assert
        assert not Attachment.objects.filter(
            file_id='wf_old_e2e',
        ).exists()
        assert Attachment.objects.filter(
            file_id='wf_new_replace_e2e',
        ).exists()
