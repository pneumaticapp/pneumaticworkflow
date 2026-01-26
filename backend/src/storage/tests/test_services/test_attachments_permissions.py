import pytest

from src.accounts.models import UserGroup
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService

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
        assert user.has_perm('access_attachment', attachment)

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
        assert owner.has_perm('access_attachment', attachment)

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
        assert member.has_perm('access_attachment', attachment)

    def test_assign_task_permissions__template_owner__ok(self):
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
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
        assert owner.has_perm('access_attachment', attachment)

    def test_assign_task_permissions__group_performer__ok(self):
        # arrange
        owner = create_test_admin()
        user_in_group = create_test_user(account=owner.account)
        group = UserGroup.objects.create(
            name='Test Group',
            account=owner.account,
        )
        group.users.add(user_in_group)
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
        assert user_in_group.has_perm('access_attachment', attachment)

    def test_assign_task_permissions__guest_performer__ok(self):
        # arrange
        owner = create_test_admin()
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
        assert guest.has_perm('access_attachment', attachment)

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
        assert not other_user.has_perm('access_attachment', attachment)


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
        assert owner.has_perm('access_attachment', attachment)

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
        assert member.has_perm('access_attachment', attachment)

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
        assert performer.has_perm('access_attachment', attachment)

    def test_assign_workflow_permissions__template_owner__ok(self):
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
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
        assert owner.has_perm('access_attachment', attachment)

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
        assert not other_user.has_perm('access_attachment', attachment)


class TestAttachmentServiceTemplatePermissions:
    """Tests for template attachment permissions."""

    def test_assign_template_permissions__owner__ok(self):
        # arrange
        owner = create_test_admin()
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
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
        assert owner.has_perm('access_attachment', attachment)

    def test_assign_template_permissions__multiple_owners__ok(self):
        # arrange
        owner1 = create_test_admin()
        owner2 = create_test_user(account=owner1.account, is_admin=True)
        template = create_test_template(owner1, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            user=owner1,
            type=OwnerType.USER,
        )
        TemplateOwner.objects.create(
            template=template,
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
        assert owner1.has_perm('access_attachment', attachment)
        assert owner2.has_perm('access_attachment', attachment)

    def test_assign_template_permissions__non_owner__no_access(self):
        # arrange
        owner = create_test_admin()
        other_user = create_test_user(account=owner.account)
        template = create_test_template(owner, is_active=True)
        TemplateOwner.objects.create(
            template=template,
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
        assert not other_user.has_perm('access_attachment', attachment)


class TestAttachmentServiceAccountPermissions:
    """Tests for account-level attachment permissions."""

    def test_check_permission__account_access__same_account__ok(
        self,
    ):
        # arrange
        user = create_test_admin()
        attachment = Attachment.objects.create(
            file_id='account_file',
            account=user.account,
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
        attachment = Attachment.objects.create(
            file_id='other_account_file',
            account=account2,
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
        attachment = Attachment.objects.create(
            file_id='public_file',
            account=account2,
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
        for attachment in attachments:
            assert performer.has_perm('access_attachment', attachment)

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
        for attachment in attachments:
            assert member.has_perm('access_attachment', attachment)

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
        for attachment in attachments:
            assert owner.has_perm('access_attachment', attachment)
