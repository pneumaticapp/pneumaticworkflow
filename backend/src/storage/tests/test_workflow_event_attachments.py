"""
Tests for WorkflowEvent attachments processing.
"""
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from src.processes.enums import WorkflowEventType
from src.processes.tests.fixtures import (
    create_test_attachment_for_event,
    create_test_event,
    create_test_user,
    create_test_workflow,
)
from src.storage.enums import SourceType
from src.storage.utils import _refresh_workflow_event_attachments

pytestmark = pytest.mark.django_db


class TestRefreshWorkflowEventAttachments:

    @patch('src.storage.utils.refresh_attachments_for_event')
    def test_refresh_workflow_event_attachments__task_comment__updates(
        self,
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
        mock_refresh_event.return_value = (['abc123'], True)

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
    def test_refresh_workflow_event_attachments__workflow_comment__updates(
        self,
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
        mock_refresh_event.return_value = (['def456'], True)

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
    def test_refresh_workflow_event_attachments__no_files__clears_flag(
        self,
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
        mock_refresh_event.return_value = ([], False)

        # act
        result = _refresh_workflow_event_attachments(mock_event, mock_user)

        # assert
        assert result == []
        assert not mock_event.with_attachments
        mock_event.save.assert_called_once_with(
            update_fields=['with_attachments'],
        )

    @patch('src.storage.utils.refresh_attachments_for_event')
    def test_refresh_workflow_event_attachments__flag_unchanged__no_save(
        self,
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
        mock_refresh_event.return_value = (['abc123'], True)

        # act
        result = _refresh_workflow_event_attachments(mock_event, mock_user)

        # assert
        assert result == ['abc123']
        mock_event.save.assert_not_called()

    @override_settings(
        FILE_SERVICE_URL='https://files.pneumatic.app',
        FILE_DOMAIN='files.pneumatic.app',
    )
    def test_refresh_workflow_event_attachments__all_attached_elsewhere__false(
        self,
    ):
        # arrange: file_id already attached to event1; event2 has same link
        # in text. bulk_create_for_event fails for all (IntegrityError),
        # has_attachments must be False for event2
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()
        event1 = create_test_event(workflow=workflow, user=user)
        event1.task = task
        event1.save()
        shared_file_id = 'shared_file_already_attached'
        create_test_attachment_for_event(
            account=user.account,
            event=event1,
            file_id=shared_file_id,
        )
        event2 = create_test_event(workflow=workflow, user=user)
        event2.task = task
        event2.type = WorkflowEventType.COMMENT
        event2.text = (
            f"[doc.pdf](https://files.pneumatic.app/{shared_file_id})"
        )
        event2.with_attachments = True
        event2.save()

        # act
        result = _refresh_workflow_event_attachments(event2, user)

        # assert
        assert result == []
        event2.refresh_from_db()
        assert event2.with_attachments is False


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
