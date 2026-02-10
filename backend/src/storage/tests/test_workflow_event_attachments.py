"""
Tests for WorkflowEvent attachments processing.
"""
from unittest.mock import Mock, patch

import pytest

from src.storage.enums import SourceType
from src.storage.utils import _refresh_workflow_event_attachments

pytestmark = pytest.mark.django_db


class TestRefreshWorkflowEventAttachments:

    @patch('src.storage.utils.refresh_attachments_for_event')
    @patch('src.storage.utils.extract_file_ids_from_text')
    def test_refresh_workflow_event_attachments__task_comment__updates(
        self,
        mock_extract,
        mock_refresh_event,
    ):
        # arrange
        mock_event = Mock()
        mock_event.task_id = 123
        mock_event.task = Mock()
        mock_event.workflow = Mock()
        mock_event.account = Mock()
        mock_event.text = (
            "[file.pdf](https://files.pneumatic.app/abc123)"
        )
        mock_event.with_attachments = False
        mock_user = Mock()
        mock_extract.return_value = ['abc123']
        mock_refresh_event.return_value = ['abc123']

        # act
        result = _refresh_workflow_event_attachments(mock_event, mock_user)

        # assert
        assert result == ['abc123']
        mock_refresh_event.assert_called_once_with(
            account=mock_event.account,
            user=mock_user,
            text=mock_event.text,
            event=mock_event,
        )
        assert mock_event.with_attachments
        mock_event.save.assert_called_once_with(
            update_fields=['with_attachments'],
        )

    @patch('src.storage.utils.refresh_attachments_for_event')
    @patch('src.storage.utils.extract_file_ids_from_text')
    def test_refresh_workflow_event_attachments__workflow_comment__updates(
        self,
        mock_extract,
        mock_refresh_event,
    ):
        # arrange
        mock_event = Mock()
        mock_event.task_id = None
        mock_event.task = None
        mock_event.workflow = Mock()
        mock_event.account = Mock()
        mock_event.text = (
            "[workflow_file.pdf]"
            "(https://files.pneumatic.app/def456)"
        )
        mock_event.with_attachments = False
        mock_user = Mock()
        mock_extract.return_value = ['def456']
        mock_refresh_event.return_value = ['def456']

        # act
        result = _refresh_workflow_event_attachments(mock_event, mock_user)

        # assert
        assert result == ['def456']
        mock_refresh_event.assert_called_once_with(
            account=mock_event.account,
            user=mock_user,
            text=mock_event.text,
            event=mock_event,
        )
        assert mock_event.with_attachments
        mock_event.save.assert_called_once_with(
            update_fields=['with_attachments'],
        )

    @patch('src.storage.utils.refresh_attachments_for_event')
    @patch('src.storage.utils.extract_file_ids_from_text')
    def test_refresh_workflow_event_attachments__no_files__clears_flag(
        self,
        mock_extract,
        mock_refresh_event,
    ):
        # arrange
        mock_event = Mock()
        mock_event.task_id = 123
        mock_event.task = Mock()
        mock_event.workflow = Mock()
        mock_event.account = Mock()
        mock_event.text = "Plain text without files"
        mock_event.with_attachments = True
        mock_user = Mock()
        mock_extract.return_value = []
        mock_refresh_event.return_value = []

        # act
        result = _refresh_workflow_event_attachments(mock_event, mock_user)

        # assert
        assert result == []
        assert not mock_event.with_attachments
        mock_event.save.assert_called_once_with(
            update_fields=['with_attachments'],
        )

    @patch('src.storage.utils.refresh_attachments_for_event')
    @patch('src.storage.utils.extract_file_ids_from_text')
    def test_refresh_workflow_event_attachments__flag_unchanged__no_save(
        self,
        mock_extract,
        mock_refresh_event,
    ):
        # arrange
        mock_event = Mock()
        mock_event.task_id = 123
        mock_event.task = Mock()
        mock_event.workflow = Mock()
        mock_event.account = Mock()
        mock_event.text = (
            "[file.pdf](https://files.pneumatic.app/abc123)"
        )
        mock_event.with_attachments = True
        mock_user = Mock()
        mock_extract.return_value = ['abc123']
        mock_refresh_event.return_value = ['abc123']

        # act
        result = _refresh_workflow_event_attachments(mock_event, mock_user)

        # assert
        assert result == ['abc123']
        mock_event.save.assert_not_called()


class TestSourceTypeFromEvent:

    def test_source_type__task_id_present__task_type(self):
        # arrange
        mock_event = Mock()
        mock_event.task_id = 123

        # act
        source_type = (
            SourceType.TASK
            if mock_event.task_id
            else SourceType.WORKFLOW
        )

        # assert
        assert source_type == SourceType.TASK

    def test_source_type__task_id_none__workflow_type(self):
        # arrange
        mock_event = Mock()
        mock_event.task_id = None

        # act
        source_type = (
            SourceType.TASK
            if mock_event.task_id
            else SourceType.WORKFLOW
        )

        # assert
        assert source_type == SourceType.WORKFLOW

    def test_source_type__task_id_zero__workflow_type(self):
        # arrange
        mock_event = Mock()
        mock_event.task_id = 0

        # act
        source_type = (
            SourceType.TASK
            if mock_event.task_id
            else SourceType.WORKFLOW
        )

        # assert
        assert source_type == SourceType.WORKFLOW
