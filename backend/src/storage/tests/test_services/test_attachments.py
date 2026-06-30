import pytest
from django.contrib.contenttypes.models import ContentType
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm

from src.permissions.models import GroupObjectPermission
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_attachment,
    create_test_group,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.services.attachments import AttachmentService
from src.storage.utils import reassign_restricted_permissions_for_task
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)

pytestmark = pytest.mark.django_db


class TestAttachmentServiceCreate:

    def test_create__account_access__ok(self):
        # arrange
        user = create_test_admin()
        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='test_file_123',
            account=user.account,
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )

        # assert
        assert service.instance is not None
        assert service.instance.file_id == 'test_file_123'
        assert service.instance.account == user.account
        assert service.instance.access_type == AccessType.ACCOUNT
        assert service.instance.source_type == SourceType.ACCOUNT

    def test_create__public_access__ok(self):
        # arrange
        user = create_test_admin()
        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='test_file_public',
            account=user.account,
            access_type=AccessType.PUBLIC,
            source_type=SourceType.ACCOUNT,
        )

        # assert
        assert service.instance.access_type == AccessType.PUBLIC

    def test_create__restricted_task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='test_file_task',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        assert service.instance.access_type == AccessType.RESTRICTED
        assert service.instance.source_type == SourceType.TASK
        assert service.instance.task == task

    def test_create__restricted_workflow__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='test_file_workflow',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        assert service.instance.source_type == SourceType.WORKFLOW
        assert service.instance.workflow == workflow


class TestAttachmentServiceBulkCreate:

    def test_bulk_create__task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=user)
        file_ids = ['file_1', 'file_2', 'file_3']

        # act
        attachments = service.bulk_create(
            file_ids=file_ids,
            source=task,
        )

        # assert
        assert len(attachments) == 3
        for attachment in attachments:
            assert attachment.account == user.account
            assert attachment.access_type == AccessType.RESTRICTED
            assert attachment.source_type == SourceType.TASK
            assert attachment.task == task

    def test_bulk_create__workflow__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        service = AttachmentService(user=user)
        file_ids = ['file_w1', 'file_w2']

        # act
        attachments = service.bulk_create(
            file_ids=file_ids,
            source=workflow,
        )

        # assert
        assert len(attachments) == 2
        for attachment in attachments:
            assert attachment.source_type == SourceType.WORKFLOW
            assert attachment.workflow == workflow

    def test_bulk_create__empty_list__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        service = AttachmentService(user=user)

        # act
        attachments = service.bulk_create(
            file_ids=[],
            source=workflow,
        )

        # assert
        assert len(attachments) == 0

    def test_bulk_create__duplicate_file_ids__ignore_conflicts(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        create_test_attachment(
            user.account,
            file_id='existing_file',
            access_type=AccessType.ACCOUNT,
            task=task,
        )

        service = AttachmentService(user=user)
        file_ids = ['existing_file', 'new_file']

        # act
        service.bulk_create(
            file_ids=file_ids,
            source=task,
        )

        # assert
        assert Attachment.objects.filter(
            file_id='new_file',
        ).exists()
        assert Attachment.objects.filter(
            task=task,
        ).count() == 2


class TestAttachmentServiceCheckPermission:

    def test_check_user_permission__public__ok(self):
        # arrange
        user = create_test_admin()
        attachment = create_test_attachment(
            user.account,
            file_id='public_file',
            access_type=AccessType.PUBLIC,
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

    def test_check_user_permission__account_same__ok(self):
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

    def test_check_user_permission__account_different__false(self):
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

    def test_check_user_permission__restricted_with_perm__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        attachment = create_test_attachment(
            user.account,
            file_id='restricted_file',
            access_type=AccessType.RESTRICTED,
            task=task,
        )

        assign_perm('storage.access_attachment', user, attachment)

        service = AttachmentService(user=user)

        # act
        result = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True

    def test_check_user_permission__restricted_no_perm__false(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        attachment = create_test_attachment(
            user.account,
            file_id='restricted_file_no_perm',
            access_type=AccessType.RESTRICTED,
            task=task,
        )

        service = AttachmentService(user=user)

        # act
        result = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is False

    def test_check_user_permission__not_exists__false(self):
        # arrange
        user = create_test_admin()
        service = AttachmentService(user=user)

        # act
        result = service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id='nonexistent_file',
        )

        # assert
        assert result is False

    def test_check_user_permission__user_not_exists__false(self):
        # arrange
        user = create_test_admin()
        attachment = create_test_attachment(
            user.account,
            file_id='file_test',
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.ACCOUNT,
        )

        service = AttachmentService(user=user)

        # act
        result = service.check_user_permission(
            user_id=99999,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is False


class TestAttachmentServiceAssignPermissions:

    def test_assign_task_permissions__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='task_perm_file',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )

        # assert
        attachment = service.instance
        assert service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

    def test_assign_workflow_permissions__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=2)

        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='workflow_perm_file',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        attachment = service.instance
        assert service.check_user_permission(
            user_id=user.id,
            account_id=user.account_id,
            file_id=attachment.file_id,
        )

    def test_create__access_type_account__no_object_permissions(self):
        # arrange
        user = create_test_admin()
        service = AttachmentService(user=user)

        # act
        service.create(
            file_id='account_perm_file',
            account=user.account,
            access_type=AccessType.ACCOUNT,
            source_type=SourceType.ACCOUNT,
        )

        # assert
        attachment = service.instance
        assert attachment.access_type == AccessType.ACCOUNT
        ctype = ContentType.objects.get_for_model(Attachment)
        obj_pk = str(attachment.pk)
        assert not UserObjectPermission.objects.filter(
            object_pk=obj_pk,
            permission__content_type=ctype,
        ).exists()
        assert not GroupObjectPermission.objects.filter(
            object_pk=obj_pk,
            content_type=ctype,
        ).exists()


class TestAttachmentDeleteGuardianCleanup:

    def test_delete__removes_guardian_permissions__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        service = AttachmentService(user=user)
        service.create(
            file_id='to_delete_restricted',
            account=user.account,
            access_type=AccessType.RESTRICTED,
            source_type=SourceType.TASK,
            task=task,
        )
        attachment = service.instance
        ctype = ContentType.objects.get_for_model(Attachment)
        obj_pk = str(attachment.pk)
        assert UserObjectPermission.objects.filter(
            object_pk=obj_pk,
            permission__content_type=ctype,
        ).exists()

        # act
        attachment.delete()

        # assert
        assert not UserObjectPermission.objects.filter(
            object_pk=obj_pk,
            permission__content_type=ctype,
        ).exists()
        assert not GroupObjectPermission.objects.filter(
            object_pk=obj_pk,
            content_type=ctype,
        ).exists()


class TestTemplateFileInheritance:
    """Tests for template file permission inheritance:
    when reassign_restricted_permissions_for_task is called,
    task participants get guardian permissions on template-level
    attachments from the same template."""

    def test_check_perm__tpl_inherit_performer__ok(self):
        """After reassign, task performer should have guardian
        permission on template attachment."""

        # arrange
        owner = create_test_admin(email='owner@pneumatic.app')
        performer = create_test_admin(
            email='performer@pneumatic.app',
            account=owner.account,
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        WorkflowPermissionService.grant_view(performer, workflow)
        attachment = create_test_attachment(
            account=owner.account,
            source_type=SourceType.TEMPLATE,
            template=workflow.template,
        )
        reassign_restricted_permissions_for_task(
            task=task,
            user=owner,
        )
        service = AttachmentService(user=performer)

        # act
        result = service.check_user_permission(
            user_id=performer.id,
            account_id=performer.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True

    def test_check_perm__tpl_inherit_outsider__denied(self):
        """User not in task/workflow should NOT get access."""

        # arrange
        owner = create_test_admin(email='owner@pneumatic.app')
        outsider = create_test_admin(
            email='outsider@pneumatic.app',
            account=owner.account,
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        attachment = create_test_attachment(
            account=owner.account,
            source_type=SourceType.TEMPLATE,
            template=workflow.template,
        )
        reassign_restricted_permissions_for_task(
            task=task,
            user=owner,
        )
        service = AttachmentService(user=outsider)

        # act
        result = service.check_user_permission(
            user_id=outsider.id,
            account_id=outsider.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is False

    def test_check_perm__tpl_inherit_wf_owner__ok(self):
        """Workflow owner should get access to template files."""

        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        attachment = create_test_attachment(
            account=owner.account,
            source_type=SourceType.TEMPLATE,
            template=workflow.template,
        )
        reassign_restricted_permissions_for_task(
            task=task,
            user=owner,
        )
        service = AttachmentService(user=owner)

        # act
        result = service.check_user_permission(
            user_id=owner.id,
            account_id=owner.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True

    def test_check_perm__tpl_inherit_group__ok(self):
        """User in a group that is a task performer should get
        access to template files via group permission."""

        # arrange
        owner = create_test_admin(email='owner@pneumatic.app')
        group_member = create_test_admin(
            email='group_member@pneumatic.app',
            account=owner.account,
        )
        group = create_test_group(
            account=owner.account,
            users=[group_member],
        )
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        TaskPerformer.objects.create(
            task=task,
            group=group,
            type=PerformerType.GROUP,
        )
        attachment = create_test_attachment(
            account=owner.account,
            source_type=SourceType.TEMPLATE,
            template=workflow.template,
        )
        reassign_restricted_permissions_for_task(
            task=task,
            user=owner,
        )
        service = AttachmentService(user=group_member)

        # act
        result = service.check_user_permission(
            user_id=group_member.id,
            account_id=group_member.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True

    def test_check_perm__tpl_inherit_cross_acc__denied(self):
        """User from a different account should NOT get access
        to template files."""

        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()
        other_account = create_test_account()
        outsider = create_test_admin(
            email='outsider@other.app',
            account=other_account,
        )
        attachment = create_test_attachment(
            account=owner.account,
            source_type=SourceType.TEMPLATE,
            template=workflow.template,
        )
        reassign_restricted_permissions_for_task(
            task=task,
            user=owner,
        )
        service = AttachmentService(user=outsider)

        # act
        result = service.check_user_permission(
            user_id=outsider.id,
            account_id=outsider.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is False

    def test_reassign__no_tpl_attachments__ok(self):
        """reassign should not fail when template has no
        restricted attachments."""

        # arrange
        owner = create_test_admin()
        workflow = create_test_workflow(user=owner, tasks_count=1)
        task = workflow.tasks.first()

        # act
        reassign_restricted_permissions_for_task(
            task=task,
            user=owner,
        )

        # assert
        assert True

    def test_check_perm__tpl_inherit_cross_task__ok(self):
        """Performer of task 2 should also get access to template
        files after reassign on task 2 (template files are shared
        across all tasks in a workflow)."""

        # arrange
        owner = create_test_admin(email='owner@pneumatic.app')
        performer_t2 = create_test_admin(
            email='performer_t2@pneumatic.app',
            account=owner.account,
        )
        workflow = create_test_workflow(user=owner, tasks_count=2)
        task_2 = workflow.tasks.all()[1]
        TaskPerformer.objects.create(
            task=task_2,
            user=performer_t2,
            type=PerformerType.USER,
        )
        WorkflowPermissionService.grant_view(performer_t2, workflow)
        attachment = create_test_attachment(
            account=owner.account,
            source_type=SourceType.TEMPLATE,
            template=workflow.template,
        )
        reassign_restricted_permissions_for_task(
            task=task_2,
            user=owner,
        )
        service = AttachmentService(user=performer_t2)

        # act
        result = service.check_user_permission(
            user_id=performer_t2.id,
            account_id=performer_t2.account_id,
            file_id=attachment.file_id,
        )

        # assert
        assert result is True
