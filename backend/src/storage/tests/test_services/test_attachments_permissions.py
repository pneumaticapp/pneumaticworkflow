import pytest

from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_guest,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.services.attachments import AttachmentService
from src.storage.utils import reassign_restricted_permissions_for_task

pytestmark = pytest.mark.django_db


class TestAttachmentServiceTaskPermissions:
    """Tests for task attachment permissions."""

    def test_assign_task_permissions__performer__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='task_performer_file',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=user)
        assert svc.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__workflow_owner__ok(self):
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__workflow_member__ok(self):
        # arrange
        owner = create_test_admin()
        member = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member)
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_member_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=member)
        assert svc.check_user_permission(
            user_id=member.id,
            account_id=member.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__template_owner__ok(self):
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        workflow = create_test_workflow(
            user=owner,
            tasks_count=1,
        )
        workflow.template = template
        workflow.save()
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_template_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__template_group_owner__ok(self):
        # arrange
        owner = create_test_admin()
        group_user1 = create_test_user(
            account=owner.account,
            email='task_template_group1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='task_template_group2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Task Template Owner Group',
            users=[group_user1, group_user2],
        )
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            group=group,
            type=OwnerType.GROUP,
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.template = template
        workflow.save()
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_template_group_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc1 = AttachmentService(user=group_user1)
        svc2 = AttachmentService(user=group_user2)
        assert svc1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__group_performer__ok(self):
        # arrange
        owner = create_test_admin()
        user_in_group = create_test_user(account=owner.account)
        group = create_test_group(
            owner.account,
            name='Test Group',
            users=[user_in_group],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_group_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=user_in_group)
        assert svc.check_user_permission(
            user_id=user_in_group.id,
            account_id=user_in_group.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__guest_performer__ok(self):
        # arrange (owner must be account_owner for GuestService.create)
        owner = create_test_owner()
        guest = create_test_guest(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=guest)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_guest_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=guest)
        assert svc.check_user_permission(
            user_id=guest.id,
            account_id=guest.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_task_permissions__non_performer__no_access(self):
        # arrange
        owner = create_test_admin()
        other_user = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='task_no_access_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=other_user)
        assert not svc.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id=attachment.file_id,
        )

    def test_reassign_restricted_permissions_for_task__new_performer__access(
        self,
    ):
        # arrange
        owner = create_test_admin()
        new_performer = create_test_user(
            account=owner.account,
            email='new_performer@test.pneumatic.app',
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)
        service.create(
            file_id='task_reassign_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance
        svc_new = AttachmentService(user=new_performer)
        assert not svc_new.check_user_permission(
            user_id=new_performer.id,
            account_id=new_performer.account_id,
            file_id=attachment.file_id,
        )
        task.taskperformer_set.create(user=new_performer)

        # act
        reassign_restricted_permissions_for_task(task=task, user=owner)

        # assert
        assert svc_new.check_user_permission(
            user_id=new_performer.id,
            account_id=new_performer.account_id,
            file_id=attachment.file_id,
        )


class TestAttachmentServiceWorkflowPermissions:
    """Tests for workflow attachment permissions."""

    def test_assign_workflow_permissions__owner__ok(self):
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='workflow_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_workflow_permissions__member__ok(self):
        # arrange
        owner = create_test_admin()
        member = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='workflow_member_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=member)
        assert svc.check_user_permission(
            user_id=member.id,
            account_id=member.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_workflow_permissions__task_performer__ok(self):
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='workflow_task_performer_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=performer)
        assert svc.check_user_permission(
            user_id=performer.id,
            account_id=performer.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_workflow_permissions__template_owner__ok(self):
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.template = template
        workflow.save()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='workflow_template_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_workflow_permissions__template_group_owner__ok(
        self,
    ):
        # arrange
        owner = create_test_admin()
        group_user1 = create_test_user(
            account=owner.account,
            email='wf_template_group1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='wf_template_group2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Workflow Template Owner Group',
            users=[group_user1, group_user2],
        )
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            group=group,
            type=OwnerType.GROUP,
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.template = template
        workflow.save()
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='workflow_template_group_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        svc1 = AttachmentService(user=group_user1)
        svc2 = AttachmentService(user=group_user2)
        assert svc1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_workflow_permissions__non_participant__no_access(
        self,
    ):
        # arrange
        owner = create_test_admin()
        other_user = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='workflow_no_access_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=other_user)
        assert not svc.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id=attachment.file_id,
        )


class TestAttachmentServiceTemplatePermissions:
    """Tests for template attachment permissions."""

    def test_assign_template_permissions__owner__ok(self):
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='template_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=template,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=owner)
        assert svc.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_template_permissions__multiple_owners__ok(self):
        # arrange
        owner1 = create_test_admin()
        owner2 = create_test_user(account=owner1.account, is_admin=True)
        template = create_test_template(owner1, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner1,
            type=OwnerType.USER,
        )
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner2,
            type=OwnerType.USER,
        )
        service = AttachmentService(user=owner1)

        # act
        service.create(
            file_id='template_multi_owner_file',
            account=owner1.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=template,
        )

        # assert
        attachment = service.instance
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

    def test_assign_template_permissions__non_owner__no_access(self):
        # arrange
        owner = create_test_admin()
        other_user = create_test_user(account=owner.account)
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=owner,
            type=OwnerType.USER,
        )
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='template_no_access_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=template,
        )

        # assert
        attachment = service.instance
        svc = AttachmentService(user=other_user)
        assert not svc.check_user_permission(
            user_id=other_user.id,
            account_id=other_user.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_template_permissions__group_owner__ok(self):
        # arrange
        owner = create_test_admin()
        group_user1 = create_test_user(
            account=owner.account,
            email='group_owner1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='group_owner2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Template Owner Group',
            users=[group_user1, group_user2],
        )
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            group=group,
            type=OwnerType.GROUP,
        )
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='template_group_owner_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=template,
        )

        # assert
        attachment = service.instance
        svc1 = AttachmentService(user=group_user1)
        svc2 = AttachmentService(user=group_user2)
        assert svc1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_template_permissions__mixed_owners__ok(self):
        # arrange
        user_owner = create_test_admin()
        group_user1 = create_test_user(
            account=user_owner.account,
            email='mixed_group1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=user_owner.account,
            email='mixed_group2@test.pneumatic.app',
        )
        individual_owner = create_test_user(
            account=user_owner.account,
            email='individual_owner@test.pneumatic.app',
            is_admin=True,
        )
        group = create_test_group(
            user_owner.account,
            name='Mixed Template Owner Group',
            users=[group_user1, group_user2],
        )
        template = create_test_template(user_owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            user=individual_owner,
            type=OwnerType.USER,
        )
        TemplateOwner.objects.create(
            template=template,
            account=template.account,
            group=group,
            type=OwnerType.GROUP,
        )
        service = AttachmentService(user=user_owner)

        # act
        service.create(
            file_id='template_mixed_owners_file',
            account=user_owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TEMPLATE,
            template=template,
        )

        # assert
        attachment = service.instance
        svc_individual = AttachmentService(user=individual_owner)
        svc_group1 = AttachmentService(user=group_user1)
        svc_group2 = AttachmentService(user=group_user2)
        assert svc_individual.check_user_permission(
            user_id=individual_owner.id,
            account_id=individual_owner.account_id,
            file_id=attachment.file_id,
        )
        assert svc_group1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_group2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )


class TestAttachmentServiceAccountPermissions:
    """Tests for account-level attachment permissions."""

    def test_check_permission__account_access__same_account__ok(
        self,
    ):
        # arrange
        user = create_test_admin()
        attachment = create_test_attachment(
            user.account,
            file_id='account_file',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user)

        # act
        result = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True

    def test_check_permission__account_access__different_account__false(
        self,
    ):
        # arrange
        account1 = create_test_account()
        user1 = create_test_admin(account=account1)
        account2 = create_test_account()
        attachment = create_test_attachment(
            account2,
            file_id='other_account_file',
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user1)

        # act
        result = service.check_user_permission(
            user_id=user1.id,
            account_id=user1.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is False

    def test_check_permission__public_access__any_user__ok(self):
        # arrange
        account1 = create_test_account()
        user1 = create_test_admin(account=account1)
        account2 = create_test_account()
        attachment = create_test_attachment(
            account2,
            file_id='public_file',
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )
        service = AttachmentService(user=user1)

        # act
        result = service.check_user_permission(
            user_id=user1.id,
            account_id=user1.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True


class TestAttachmentServiceGroupPermissions:
    """Tests for group-based attachment permissions."""

    def test_task_group_performer_multiple_users__all_have_access__ok(
        self,
    ):
        """
        Scenario: Task with group performer containing multiple users
        Expected: All users in group have access to attachment
        """
        # arrange
        owner = create_test_admin()
        user1 = create_test_user(
            account=owner.account,
            email='group_user1@test.pneumatic.app',
        )
        user2 = create_test_user(
            account=owner.account,
            email='group_user2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Test Group Multiple',
            users=[user1, user2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='group_multi_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc1 = AttachmentService(user=user1)
        svc2 = AttachmentService(user=user2)
        assert svc1.check_user_permission(
            user_id=user1.id,
            account_id=user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc2.check_user_permission(
            user_id=user2.id,
            account_id=user2.account_id,
            file_id=attachment.file_id,
        )

    def test_task_mixed_performers__all_have_access__ok(self):
        """
        Scenario: Task with both group and individual performers
        Expected: Both group users and individual user have access
        """
        # arrange
        owner = create_test_admin()
        individual_user = create_test_user(
            account=owner.account,
            email='individual@test.pneumatic.app',
        )
        group_user1 = create_test_user(
            account=owner.account,
            email='group1@test.pneumatic.app',
        )
        group_user2 = create_test_user(
            account=owner.account,
            email='group2@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Mixed Test Group',
            users=[group_user1, group_user2],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=individual_user)
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='mixed_performers_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc_individual = AttachmentService(user=individual_user)
        svc_group1 = AttachmentService(user=group_user1)
        svc_group2 = AttachmentService(user=group_user2)
        assert svc_individual.check_user_permission(
            user_id=individual_user.id,
            account_id=individual_user.account_id,
            file_id=attachment.file_id,
        )
        assert svc_group1.check_user_permission(
            user_id=group_user1.id,
            account_id=group_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_group2.check_user_permission(
            user_id=group_user2.id,
            account_id=group_user2.account_id,
            file_id=attachment.file_id,
        )

    def test_user_removed_from_group__loses_access__ok(self):
        """
        Scenario: User removed from group that was task performer
        Expected: User loses access after removal from group
        """
        # arrange
        owner = create_test_admin()
        user_in_group = create_test_user(
            account=owner.account,
            email='removable@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Removable Group',
            users=[user_in_group],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)
        service.create(
            file_id='removable_group_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance
        svc = AttachmentService(user=user_in_group)
        assert svc.check_user_permission(
            user_id=user_in_group.id,
            account_id=user_in_group.account_id,
            file_id=attachment.file_id,
        )

        # act
        group.users.remove(user_in_group)

        # assert
        svc_after = AttachmentService(user=user_in_group)
        assert not svc_after.check_user_permission(
            user_id=user_in_group.id,
            account_id=user_in_group.account_id,
            file_id=attachment.file_id,
        )

    def test_user_added_to_group__gains_access__ok(self):
        """
        Scenario: User added to group that is task performer
        Expected: User gains access after addition to group
        """
        # arrange
        owner = create_test_admin()
        new_user = create_test_user(
            account=owner.account,
            email='new_group_user@test.pneumatic.app',
        )
        existing_user = create_test_user(
            account=owner.account,
            email='existing@test.pneumatic.app',
        )
        group = create_test_group(
            owner.account,
            name='Expandable Group',
            users=[existing_user],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group)
        service = AttachmentService(user=owner)
        service.create(
            file_id='expandable_group_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance
        svc_new = AttachmentService(user=new_user)
        assert not svc_new.check_user_permission(
            user_id=new_user.id,
            account_id=new_user.account_id,
            file_id=attachment.file_id,
        )

        # act
        group.users.add(new_user)

        # assert
        svc_after = AttachmentService(user=new_user)
        assert svc_after.check_user_permission(
            user_id=new_user.id,
            account_id=new_user.account_id,
            file_id=attachment.file_id,
        )

    def test_multiple_groups_same_task__all_users_have_access__ok(
        self,
    ):
        """
        Scenario: Task with multiple group performers
        Expected: All users from all groups have access
        """
        # arrange
        owner = create_test_admin()
        group1_user1 = create_test_user(
            account=owner.account,
            email='g1u1@test.pneumatic.app',
        )
        group1_user2 = create_test_user(
            account=owner.account,
            email='g1u2@test.pneumatic.app',
        )
        group2_user1 = create_test_user(
            account=owner.account,
            email='g2u1@test.pneumatic.app',
        )
        group1 = create_test_group(
            owner.account,
            name='Group 1',
            users=[group1_user1, group1_user2],
        )
        group2 = create_test_group(
            owner.account,
            name='Group 2',
            users=[group2_user1],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(group=group1)
        task.taskperformer_set.create(group=group2)
        service = AttachmentService(user=owner)

        # act
        service.create(
            file_id='multi_groups_file',
            account=owner.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        svc_g1u1 = AttachmentService(user=group1_user1)
        svc_g1u2 = AttachmentService(user=group1_user2)
        svc_g2u1 = AttachmentService(user=group2_user1)
        assert svc_g1u1.check_user_permission(
            user_id=group1_user1.id,
            account_id=group1_user1.account_id,
            file_id=attachment.file_id,
        )
        assert svc_g1u2.check_user_permission(
            user_id=group1_user2.id,
            account_id=group1_user2.account_id,
            file_id=attachment.file_id,
        )
        assert svc_g2u1.check_user_permission(
            user_id=group2_user1.id,
            account_id=group2_user1.account_id,
            file_id=attachment.file_id,
        )


class TestAttachmentServiceBulkCreatePermissions:
    """Tests for bulk_create permissions assignment."""

    def test_bulk_create__task__assigns_permissions__ok(self):
        # arrange
        owner = create_test_admin()
        performer = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        task.taskperformer_set.create(user=performer)
        service = AttachmentService(user=owner)
        file_ids = ['bulk_file_1', 'bulk_file_2']

        # act
        attachments = service.bulk_create(
            file_ids=file_ids,
            source=task,
        )

        # assert
        svc = AttachmentService(user=performer)
        for attachment in attachments:
            assert svc.check_user_permission(
                user_id=performer.id,
                account_id=performer.account_id,
                file_id=attachment.file_id,
            )

    def test_bulk_create__workflow__assigns_permissions__ok(self):
        # arrange
        owner = create_test_admin()
        member = create_test_user(account=owner.account)
        workflow = create_test_workflow(user=owner, tasks_count=1)
        workflow.members.add(member)
        service = AttachmentService(user=owner)
        file_ids = ['bulk_wf_1', 'bulk_wf_2']

        # act
        attachments = service.bulk_create(
            file_ids=file_ids,
            source=workflow,
        )

        # assert
        svc = AttachmentService(user=member)
        for attachment in attachments:
            assert svc.check_user_permission(
                user_id=member.id,
                account_id=member.account_id,
                file_id=attachment.file_id,
            )

    def test_bulk_create_for_scope__assigns_permissions__ok(self):
        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=owner)
        file_ids = ['scope_file_1', 'scope_file_2']

        # act
        attachments = service.bulk_create_for_scope(
            file_ids=file_ids,
            account=owner.account,
            source_type=SourceType.TASK,
            access_type=AccessType.RESTRICTED,
            task=task,
        )

        # assert
        assert len(attachments) == 2
        svc = AttachmentService(user=owner)
        for attachment in attachments:
            assert svc.check_user_permission(
                user_id=owner.id,
                account_id=owner.account_id,
                file_id=attachment.file_id,
            )
