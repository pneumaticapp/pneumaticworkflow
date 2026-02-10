"""
Tests for refresh_attachments and related utilities.
"""
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Task
from src.storage.enums import SourceType
from src.storage.utils import (
    extract_file_ids_from_text,
    refresh_attachments,
    refresh_attachments_for_text,
)

pytestmark = pytest.mark.django_db


class TestExtractFileIdsFromText:

    @override_settings(
        FILE_SERVICE_URL='https://files.pneumatic.app',
        FILE_DOMAIN='files.pneumatic.app',
    )
    def test_extract_file_ids_from_text__single_link__list_with_one_id(self):
        # arrange
        text = "[document.pdf](https://files.pneumatic.app/abc123def456)"

        # act
        file_ids = extract_file_ids_from_text(text)

        # assert
        assert file_ids == ['abc123def456']

    @override_settings(
        FILE_SERVICE_URL='https://files.pneumatic.app',
        FILE_DOMAIN='files.pneumatic.app',
    )
    def test_extract_file_ids_from_text__multiple_links__set_of_internal_ids(
        self,
    ):
        # arrange
        text = """
        Documents:
        [contract.pdf](https://files.pneumatic.app/abc12345)
        [specification.docx](https://files.pneumatic.app/def45678)
        [external.pdf](https://drive.google.com/d/xyz789)
        """

        # act
        file_ids = extract_file_ids_from_text(text)

        # assert
        assert set(file_ids) == {'abc12345', 'def45678'}

    def test_extract_file_ids_from_text__no_links__empty_list(self):
        # arrange
        text = "Plain text without files"

        # act
        file_ids = extract_file_ids_from_text(text)

        # assert
        assert file_ids == []

    @override_settings(
        FILE_SERVICE_URL='https://files.pneumatic.app',
        FILE_DOMAIN='files.pneumatic.app',
    )
    def test_extract_file_ids_from_text__external_links__ignored(self):
        # arrange
        text = """
        [internal.pdf](https://files.pneumatic.app/internal123)
        [external.pdf](https://drive.google.com/d/external456)
        [sharepoint.docx](https://company.sharepoint.com/doc.docx)
        """

        # act
        file_ids = extract_file_ids_from_text(text)

        # assert
        assert file_ids == ['internal123']


class TestRefreshAttachmentsForText:

    @override_settings(
        FILE_SERVICE_URL='https://files.pneumatic.app',
        FILE_DOMAIN='files.pneumatic.app',
    )
    @patch('src.storage.utils.AttachmentService')
    @patch('src.storage.utils.Attachment.objects')
    def test_refresh_attachments_for_text__new_file_ids__creates_and_returns(
        self,
        mock_attachment_objects,
        mock_service_class,
    ):
        # arrange
        mock_user = Mock()
        mock_account = Mock()
        mock_account.id = 1
        mock_filter = mock_attachment_objects.filter.return_value
        mock_filter.values_list.return_value = []
        mock_filter.exclude.return_value.delete.return_value = (0, {})
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        text = "[test.pdf](https://files.pneumatic.app/test12345)"
        mock_task = Mock()

        # act
        result = refresh_attachments_for_text(
            account=mock_account,
            user=mock_user,
            text=text,
            source_type=SourceType.TASK,
            task=mock_task,
        )

        # assert
        assert result == ['test12345']
        mock_service.bulk_create_for_scope.assert_called_once_with(
            file_ids=['test12345'],
            account=mock_account,
            source_type=SourceType.TASK,
            task=mock_task,
            workflow=None,
            template=None,
        )

    @patch('src.storage.utils.Attachment.objects')
    def test_refresh_attachments_for_text__empty_text__deletes_unused(
        self,
        mock_attachment_objects,
    ):
        # arrange
        mock_user = Mock()
        mock_account = Mock()
        mock_account.id = 1
        mock_filter = mock_attachment_objects.filter.return_value
        mock_filter.delete.return_value = (2, {})

        # act
        result = refresh_attachments_for_text(
            account=mock_account,
            user=mock_user,
            text="",
            source_type=SourceType.TASK,
            task=Mock(),
        )

        # assert
        assert result == []
        mock_attachment_objects.filter.assert_called()


class TestRefreshAttachments:

    @patch('src.storage.utils._refresh_task_attachments')
    def test_refresh_attachments__task_source__calls_task_refresh(
        self,
        mock_refresh_task,
    ):
        # arrange
        mock_task = Mock(spec=Task)
        mock_user = Mock()
        mock_refresh_task.return_value = ['file123']

        # act
        result = refresh_attachments(mock_task, mock_user)

        # assert
        assert result == ['file123']
        mock_refresh_task.assert_called_once_with(mock_task, mock_user)

    @patch('src.storage.utils._refresh_workflow_event_attachments')
    def test_refresh_attachments__workflow_event_source__calls_event_refresh(
        self,
        mock_refresh_event,
    ):
        # arrange
        mock_event = Mock(spec=WorkflowEvent)
        mock_user = Mock()
        mock_refresh_event.return_value = ['event123']

        # act
        result = refresh_attachments(mock_event, mock_user)

        # assert
        assert result == ['event123']
        mock_refresh_event.assert_called_once_with(mock_event, mock_user)

    def test_refresh_attachments__unsupported_source__empty_list(self):
        # arrange
        mock_source = Mock()
        mock_user = Mock()

        # act
        result = refresh_attachments(mock_source, mock_user)

        # assert
        assert result == []
