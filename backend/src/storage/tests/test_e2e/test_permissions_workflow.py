"""
E2E tests for permissions workflow across different scenarios.
Tests full workflow without mocks - real database operations.
"""
import pytest
from guardian.shortcuts import assign_perm

from src.accounts.models import UserGroup
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

pytestmark = pytest.mark.django_db


class TestPermissionsWorkflowE2E:
    """
    End-to-end tests for permissions across different scenarios.
    """

    def test_public_access__any_user__ok(self):
        """
        Scenario: Public attachment
        Expected: Any user can access
        """
        # arrange
        account1 = create_test_account()
        create_test_admin(account=account1)
        account2 = create_test_account()
        user2 = create_test_admin(account=account2)
        attachment = Attachment.objects.create(
            file_id='public_e2e',
            account=account1,
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user2)

        # act
        has_access = service.check_user_permission(
            user_id=user2.id,
            account_id=user2.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert has_access is True

    def test_account_access__same_account__ok(self):
        """
        Scenario: Account-level attachment
        Expected: All users from same account can access
        """
        # arrange
        account = create_test_account()
        create_test_admin(account=account)
        user2 = create_test_user(account=account)
        attachment = Attachment.objects.create(
            file_id='account_e2e',
            account=account,
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user2)

        # act
        has_access = service.check_user_permission(
            user_id=user2.id,
            account_id=user2.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert has_access is True

    def test_account_access__different_account__forbidden(self):
        """
        Scenario: Account-level attachment, user from different account
        Expected: Access denied
        """
        # arrange
        account1 = create_test_account()
        account2 = create_test_account()
        create_test_admin(account=account1)
        user2 = create_test_admin(account=account2)
        attachment = Attachment.objects.create(
            file_id='account_diff_e2e',
            account=account1,
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user2)

        # act
        has_access = service.check_user_permission(
            user_id=user2.id,
            account_id=user2.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert has_access is False

    def test_restricted_access__with_permission__ok(self):
        """
        Scenario: Restricted attachment with explicit permission
        Expected: User with permission can access
        """
        # arrange
        user = create_test_admin()
        attachment = Attachment.objects.create(
            file_id='restricted_e2e',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        assign_perm('access_attachment', user, attachment)
        service = AttachmentService(user=user)

        # act
        has_access = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert has_access is True

    def test_restricted_access__without_permission__forbidden(self):
        """
        Scenario: Restricted attachment without permission
        Expected: Access denied
        """
        # arrange
        user = create_test_admin()
        attachment = Attachment.objects.create(
            file_id='restricted_no_perm_e2e',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user)

        # act
        has_access = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert has_access is False

    def test_group_permission__user_in_group__ok(self):
        """
        Scenario: Group has permission, user is in group
        Expected: User can access via group permission
        """
        # arrange
        owner = create_test_admin()
        user_in_group = create_test_user(account=owner.account)
        group = UserGroup.objects.create(
            name='Test Group E2E',
            account=owner.account,
        )
        group.users.add(user_in_group)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)
        service.create(
            file_id='group_perm_e2e',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance

        # act
        has_access = user_in_group.has_perm(
            'access_attachment',
            attachment,
        )

        # assert
        assert has_access is True

    def test_group_permission__user_not_in_group__forbidden(self):
        """
        Scenario: Group has permission, user not in group
        Expected: Access denied
        """
        # arrange
        owner = create_test_admin()
        user_not_in_group = create_test_user(account=owner.account)
        group = UserGroup.objects.create(
            name='Test Group E2E 2',
            account=owner.account,
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)
        service.create(
            file_id='group_no_perm_e2e',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance

        # act
        has_access = user_not_in_group.has_perm(
            'access_attachment',
            attachment,
        )

        # assert
        assert has_access is False

    def test_guest_user__with_permission__ok(self):
        """
        Scenario: Guest user with permission
        Expected: Guest can access
        """
        # arrange
        owner = create_test_admin()
        guest = create_test_guest(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=guest)
        service = AttachmentService(user=owner)
        service.create(
            file_id='guest_perm_e2e',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance

        # act
        has_access = guest.has_perm('access_attachment', attachment)

        # assert
        assert has_access is True

    def test_nonexistent_file__forbidden(self):
        """
        Scenario: Check permission for nonexistent file
        Expected: Access denied
        """
        # arrange
        user = create_test_admin()
        service = AttachmentService(user=user)

        # act
        has_access = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id='nonexistent_e2e',
        )

        # assert
        assert has_access is False

    def test_nonexistent_user__forbidden(self):
        """
        Scenario: Check permission for nonexistent user
        Expected: Access denied
        """
        # arrange
        user = create_test_admin()
        attachment = Attachment.objects.create(
            file_id='user_not_exists_e2e',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user)

        # act
        has_access = service.check_user_permission(
            user_id=999999,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert has_access is False

    def test_get_user_attachments__mixed_access_types__ok(self):
        """
        Scenario: User has access to attachments via different methods
        Expected: Returns all accessible attachments
        """
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        other_account = create_test_account()

        # Public attachment from other account
        Attachment.objects.create(
            file_id='mixed_public_e2e',
            account=other_account,
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )

        # Account attachment from same account
        Attachment.objects.create(
            file_id='mixed_account_e2e',
            account=account,
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )

        # Restricted attachment with permission
        restricted_att = Attachment.objects.create(
            file_id='mixed_restricted_e2e',
            account=account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )
        assign_perm('access_attachment', user, restricted_att)

        # Restricted attachment without permission
        Attachment.objects.create(
            file_id='mixed_no_access_e2e',
            account=account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )

        service = AttachmentService(user=user)

        # act
        user_attachments = service.get_user_attachments(user)

        # assert
        file_ids = [a.file_id for a in user_attachments]
        assert 'mixed_public_e2e' in file_ids
        assert 'mixed_account_e2e' in file_ids
        assert 'mixed_restricted_e2e' in file_ids
        assert 'mixed_no_access_e2e' not in file_ids

    def test_cascade_permissions__workflow_to_tasks__ok(self):
        """
        Scenario: User has access to workflow and all its tasks
        Expected: User can access attachments from workflow and tasks
        """
        # arrange
        owner = create_test_admin()
        member = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=2)
        workflow.members.add(member)
        task1 = workflow.tasks.first()
        task2 = workflow.tasks.last()

        # Create attachments
        service = AttachmentService(user=owner)
        service.create(
            file_id='cascade_workflow_e2e',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )
        wf_attachment = service.instance

        service.create(
            file_id='cascade_task1_e2e',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task1,
        )
        task1_attachment = service.instance

        service.create(
            file_id='cascade_task2_e2e',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task2,
        )
        task2_attachment = service.instance

        # act & assert
        assert member.has_perm('access_attachment', wf_attachment)
        assert member.has_perm('access_attachment', task1_attachment)
        assert member.has_perm('access_attachment', task2_attachment)
