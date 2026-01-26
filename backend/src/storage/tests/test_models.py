import pytest

from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

pytestmark = pytest.mark.django_db


class TestAttachmentModel:

    def test_create__minimal_fields__ok(self):
        # arrange
        account = create_test_account()

        # act
        attachment = Attachment.objects.create(
            file_id='test_file_123',
            account=account,
            source_type=SourceType.ACCOUNT,
        )

        # assert
        assert attachment.file_id == 'test_file_123'
        assert attachment.account == account
        assert attachment.source_type == SourceType.ACCOUNT
        assert attachment.access_type == AccessType.ACCOUNT
        assert attachment.task is None
        assert attachment.workflow is None
        assert attachment.template is None

    def test_create__with_task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        # act
        attachment = Attachment.objects.create(
            file_id='task_file_123',
            account=user.account,
            source_type=SourceType.TASK,
            task=task,
            access_type=AccessType.RESTRICTED,
        )

        # assert
        assert attachment.task == task
        assert attachment.source_type == SourceType.TASK
        assert attachment.access_type == AccessType.RESTRICTED

    def test_create__with_workflow__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)

        # act
        attachment = Attachment.objects.create(
            file_id='workflow_file_123',
            account=user.account,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # assert
        assert attachment.workflow == workflow
        assert attachment.source_type == SourceType.WORKFLOW

    def test_str__ok(self):
        # arrange
        account = create_test_account()
        attachment = Attachment.objects.create(
            file_id='test_file_str',
            account=account,
            source_type=SourceType.ACCOUNT,
        )

        # act
        result = str(attachment)

        # assert
        assert 'test_file_str' in result
        assert SourceType.ACCOUNT in result

    def test_soft_delete__ok(self):
        # arrange
        account = create_test_account()
        attachment = Attachment.objects.create(
            file_id='soft_delete_test',
            account=account,
            source_type=SourceType.ACCOUNT,
        )

        # act
        attachment.is_deleted = True
        attachment.save()

        # assert
        assert Attachment.objects.filter(
            file_id='soft_delete_test',
            is_deleted=False,
        ).count() == 0
        assert Attachment.objects.filter(
            file_id='soft_delete_test',
        ).count() == 1

    def test_cascade_delete__task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        Attachment.objects.create(
            file_id='cascade_task',
            account=user.account,
            source_type=SourceType.TASK,
            task=task,
        )

        # act
        task.delete()

        # assert
        assert not Attachment.objects.filter(
            file_id='cascade_task',
        ).exists()

    def test_cascade_delete__workflow__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        Attachment.objects.create(
            file_id='cascade_workflow',
            account=user.account,
            source_type=SourceType.WORKFLOW,
            workflow=workflow,
        )

        # act
        workflow.delete()

        # assert
        assert not Attachment.objects.filter(
            file_id='cascade_workflow',
        ).exists()

    def test_related_name__task__ok(self):
        # arrange
        user = create_test_admin()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        Attachment.objects.create(
            file_id='related_task_1',
            account=user.account,
            source_type=SourceType.TASK,
            task=task,
        )
        Attachment.objects.create(
            file_id='related_task_2',
            account=user.account,
            source_type=SourceType.TASK,
            task=task,
        )

        # act
        attachments = task.storage_attachments.all()

        # assert
        assert attachments.count() == 2

    def test_index__file_id__ok(self):
        # arrange
        account = create_test_account()
        Attachment.objects.create(
            file_id='indexed_file',
            account=account,
            source_type=SourceType.ACCOUNT,
        )

        # act
        attachment = Attachment.objects.filter(
            file_id='indexed_file',
        ).first()

        # assert
        assert attachment is not None

    def test_index__source_type_account__ok(self):
        # arrange
        account = create_test_account()
        Attachment.objects.create(
            file_id='source_indexed',
            account=account,
            source_type=SourceType.ACCOUNT,
        )

        # act
        attachments = Attachment.objects.filter(
            source_type=SourceType.ACCOUNT,
            account=account,
        )

        # assert
        assert attachments.count() >= 1
