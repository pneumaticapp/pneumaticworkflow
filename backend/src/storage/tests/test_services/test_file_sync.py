import pytest

from src.processes.models.workflows.attachment import FileAttachment
from src.processes.tests.fixtures import (
    create_test_attachment,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import SourceType
from src.storage.models import Attachment
from src.storage.services.file_sync import FileSyncService

pytestmark = pytest.mark.django_db


class TestFileSyncServiceSyncAllFiles:

    def test_sync_all_files__empty__ok(self, mocker):
        # arrange
        service = FileSyncService()
        mocker.patch.object(
            service,
            '_generate_file_id',
            return_value='generated_file_id',
        )

        # act
        stats = service.sync_all_files()

        # assert
        assert stats['total'] == 0
        assert stats['synced'] == 0
        assert stats['skipped'] == 0
        assert stats['errors'] == 0

    def test_sync_all_files__success__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()
        generate_mock = mocker.patch.object(
            service,
            '_generate_file_id',
            return_value='generated_file_id_123',
        )
        create_mock = mocker.patch.object(
            service,
            '_create_file_service_record',
            return_value=True,
        )

        # act
        stats = service.sync_all_files()

        # assert
        assert stats['total'] == 1
        assert stats['synced'] == 1
        assert stats['skipped'] == 0
        assert stats['errors'] == 0

        attachment.refresh_from_db()
        assert attachment.file_id == 'generated_file_id_123'
        generate_mock.assert_called_once_with(attachment)
        create_mock.assert_called_once_with(
            attachment,
            'generated_file_id_123',
        )

    def test_sync_all_files__skipped__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()
        mocker.patch.object(
            service,
            '_generate_file_id',
            return_value=None,
        )

        # act
        stats = service.sync_all_files()

        # assert
        assert stats['total'] == 1
        assert stats['synced'] == 0
        assert stats['skipped'] == 1
        assert stats['errors'] == 0

    def test_sync_all_files__error__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()
        mocker.patch.object(
            service,
            '_generate_file_id',
            return_value='file_id_123',
        )
        mocker.patch.object(
            service,
            '_create_file_service_record',
            return_value=False,
        )

        # act
        stats = service.sync_all_files()

        # assert
        assert stats['total'] == 1
        assert stats['synced'] == 0
        assert stats['skipped'] == 0
        assert stats['errors'] == 1

    def test_sync_all_files__already_synced__not_included(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
            file_id='already_has_file_id',
        )

        service = FileSyncService()
        generate_mock = mocker.patch.object(
            service,
            '_generate_file_id',
        )

        # act
        stats = service.sync_all_files()

        # assert
        assert stats['total'] == 0
        generate_mock.assert_not_called()


class TestFileSyncServiceCreateFileServiceRecord:

    def test_create_file_service_record__success__ok(self):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()

        # act
        result = service._create_file_service_record(
            attachment,
            'generated_file_id_123',
        )

        # assert
        assert result is True


class TestFileSyncServiceSyncToNewAttachmentModel:

    def test_sync_to_new_attachment_model__success__ok(self):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        old_attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            file_id='old_file_id_123',
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()

        # act
        stats = service.sync_to_new_attachment_model([old_attachment])

        # assert
        assert stats['total'] == 1
        assert stats['created'] == 1
        assert stats['skipped'] == 0
        assert stats['errors'] == 0

        new_attachment = Attachment.objects.get(
            file_id='old_file_id_123',
        )
        assert new_attachment.account == user.account
        assert new_attachment.workflow == workflow

    def test_sync_to_new_attachment_model__no_file_id__skipped(self):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        old_attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()

        # act
        stats = service.sync_to_new_attachment_model([old_attachment])

        # assert
        assert stats['total'] == 1
        assert stats['created'] == 0
        assert stats['skipped'] == 1
        assert stats['errors'] == 0

    def test_sync_to_new_attachment_model__empty_list__ok(self):
        # arrange
        service = FileSyncService()

        # act
        stats = service.sync_to_new_attachment_model([])

        # assert
        assert stats['total'] == 0
        assert stats['created'] == 0
        assert stats['skipped'] == 0
        assert stats['errors'] == 0

    def test_sync_to_new_attachment_model__already_exists__skipped(self):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        old_attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            file_id='existing_file_id',
            account=user.account,
            workflow=workflow,
        )

        create_test_attachment(
            user.account,
            file_id='existing_file_id',
            workflow=workflow,
        )

        service = FileSyncService()

        # act
        stats = service.sync_to_new_attachment_model([old_attachment])

        # assert
        assert stats['total'] == 1
        assert stats['created'] == 0
        assert stats['skipped'] == 1
        assert Attachment.objects.filter(
            file_id='existing_file_id',
        ).count() == 1


class TestFileSyncServiceDetermineSourceType:

    def test_determine_source_type__workflow__ok(self):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()

        # act
        result = service._determine_source_type(attachment)

        # assert
        assert result == SourceType.WORKFLOW

    def test_determine_source_type__task_via_event__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        event_mock = mocker.Mock()
        event_mock.task = task

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
        )
        mocker.patch.object(
            type(attachment),
            'event',
            new_callable=mocker.PropertyMock,
            return_value=event_mock,
        )

        service = FileSyncService()

        # act
        result = service._determine_source_type(attachment)

        # assert
        assert result == SourceType.TASK

    def test_determine_source_type__workflow_via_event__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        event_mock = mocker.Mock()
        event_mock.task = None

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )
        mocker.patch.object(
            type(attachment),
            'event',
            new_callable=mocker.PropertyMock,
            return_value=event_mock,
        )

        service = FileSyncService()

        # act
        result = service._determine_source_type(attachment)

        # assert
        assert result == SourceType.WORKFLOW

    def test_determine_source_type__task_via_output__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        output_mock = mocker.Mock()
        output_mock.task = task

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
        )
        mocker.patch.object(
            type(attachment),
            'output',
            new_callable=mocker.PropertyMock,
            return_value=output_mock,
        )

        service = FileSyncService()

        # act
        result = service._determine_source_type(attachment)

        # assert
        assert result == SourceType.TASK

    def test_determine_source_type__account__ok(self):
        # arrange
        user = create_test_user()

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
        )

        service = FileSyncService()

        # act
        result = service._determine_source_type(attachment)

        # assert
        assert result == SourceType.ACCOUNT


class TestFileSyncServiceGetTask:

    def test_get_task__via_event__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        event_mock = mocker.Mock()
        event_mock.task = task

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
        )
        mocker.patch.object(
            type(attachment),
            'event',
            new_callable=mocker.PropertyMock,
            return_value=event_mock,
        )

        service = FileSyncService()

        # act
        result = service._get_task(attachment)

        # assert
        assert result == task

    def test_get_task__via_output__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        output_mock = mocker.Mock()
        output_mock.task = task

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
        )
        mocker.patch.object(
            type(attachment),
            'output',
            new_callable=mocker.PropertyMock,
            return_value=output_mock,
        )

        service = FileSyncService()

        # act
        result = service._get_task(attachment)

        # assert
        assert result == task

    def test_get_task__no_task__none(self):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)

        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
            workflow=workflow,
        )

        service = FileSyncService()

        # act
        result = service._get_task(attachment)

        # assert
        assert result is None


class TestFileSyncServiceGenerateFileId:

    def test_generate_file_id__ok(self, mocker):
        # arrange
        user = create_test_user()
        attachment = FileAttachment.objects.create(
            name='test.pdf',
            url='https://storage.com/test.pdf',
            size=1024,
            account=user.account,
        )
        mocker.patch(
            'src.storage.services.file_sync.get_salt',
            return_value='random_salt_32_chars',
        )

        service = FileSyncService()

        # act
        result = service._generate_file_id(attachment)

        # assert
        assert result is not None
        assert 'random_salt_32_chars' in result
        assert 'test.pdf' in result
