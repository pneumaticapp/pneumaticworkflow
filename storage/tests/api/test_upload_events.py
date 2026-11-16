"""Tests for the record the upload endpoint writes into the journal."""

import json
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock

from src.application.dto import UploadFileCommand
from src.shared_kernel.auth.user_types import JournalUserType
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.events.schema import (
    SERVICE_NAME,
    Actor,
    Event,
    EventName,
    RequestContext,
)
from src.shared_kernel.exceptions import DomainFileNotFoundError
from tests.fixtures.unit import (
    API_FILE_ID as FILE_ID,
    EMITTER_MAXLEN,
    EMITTER_STREAM_KEY,
)


def test_upload__ok__upload_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_response,
    mock_upload_use_case_execute,
    capturing_emitter,
    mock_request_events_now,
    mocker,
):
    # arrange
    mock_upload_use_case_execute.return_value = mock_upload_response
    get_event_emitter_mock = mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=capturing_emitter,
    )

    # act
    response = e2e_client.post(
        '/upload',
        files={'file': ('test.txt', sample_file_content, 'text/plain')},
        headers={**auth_headers, 'X-Request-ID': 'req-1'},
    )

    # assert
    assert response.status_code == 200
    assert capturing_emitter.events == [
        Event(
            type=EventName.FILE_UPLOAD,
            service=SERVICE_NAME,
            ts=datetime(2026, 9, 9, 12, 0, 0, 123, tzinfo=UTC),
            account_id=1,
            actor=Actor(id=1, user_type=JournalUserType.USER),
            auth_type='User',
            file_id='12345678-1234-5678-1234-567812345679',
            context=RequestContext(
                ip='testclient',
                user_agent='testclient',
                request_id='req-1',
            ),
            payload={
                'filename': 'test.txt',
                'size': 17,
                'content_type': 'text/plain',
            },
        ),
    ]
    get_event_emitter_mock.assert_called_once_with()
    mock_request_events_now.assert_called_once_with()
    mock_upload_use_case_execute.assert_awaited_once_with(
        UploadFileCommand(
            file_stream=ANY,
            filename='test.txt',
            content_type='text/plain',
            size=17,
            user_id=1,
            account_id=1,
        ),
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_upload__use_case_failed__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_use_case_execute,
    mock_events_file_upload,
):
    # arrange
    mock_upload_use_case_execute.side_effect = DomainFileNotFoundError(
        file_id=FILE_ID,
    )

    # act
    response = e2e_client.post(
        '/upload',
        files={'file': ('test.txt', sample_file_content, 'text/plain')},
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 404
    mock_events_file_upload.assert_not_awaited()
    mock_upload_use_case_execute.assert_awaited_once_with(
        UploadFileCommand(
            file_stream=ANY,
            filename='test.txt',
            content_type='text/plain',
            size=17,
            user_id=1,
            account_id=1,
        ),
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_upload__file_too_large__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_use_case_execute,
    mock_events_file_upload,
    mocker,
):
    # arrange
    settings = BaseAppSettings(
        DJANGO_SECRET_KEY='test-key',
        MAX_FILE_SIZE=5,
    )
    get_settings_mock = mocker.patch(
        'src.shared_kernel.di.container.get_settings',
        return_value=settings,
    )

    # act
    response = e2e_client.post(
        '/upload',
        files={'file': ('test.txt', sample_file_content, 'text/plain')},
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 413
    mock_events_file_upload.assert_not_awaited()
    mock_upload_use_case_execute.assert_not_awaited()
    get_settings_mock.assert_called_once_with()
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_upload__events_stream_unavailable__file_uploaded(
    e2e_client,
    mock_auth_middleware,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_response,
    mock_upload_use_case_execute,
    events_emitter,
    mock_events_redis_from_url,
    mock_request_events_now,
    mocker,
):
    # arrange
    mock_upload_use_case_execute.return_value = mock_upload_response
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = ConnectionError('refused')
    mock_events_redis_from_url.return_value = client_mock
    get_event_emitter_mock = mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=events_emitter,
    )

    # act
    response = e2e_client.post(
        '/upload',
        files={'file': ('test.txt', sample_file_content, 'text/plain')},
        headers={**auth_headers, 'X-Request-ID': 'req-1'},
    )

    # assert
    assert response.status_code == 200
    assert response.json() == {
        'public_url': (
            'http://localhost:8000/12345678-1234-5678-1234-567812345679'
        ),
        'file_id': '12345678-1234-5678-1234-567812345679',
    }
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields={
            'type': 'file.upload',
            'data': json.dumps(
                {
                    'type': 'file.upload',
                    'category': 'files',
                    'service': 'pneumatic-file-service',
                    'ts': '2026-09-09T12:00:00.000123Z',
                    'account_id': 1,
                    'actor': {'id': 1, 'email': None, 'user_type': 'user'},
                    'auth_type': 'User',
                    'object': {
                        'type': 'file',
                        'id': '12345678-1234-5678-1234-567812345679',
                    },
                    'workflow_id': None,
                    'task_id': None,
                    'ip': 'testclient',
                    'user_agent': 'testclient',
                    'request_id': 'req-1',
                    'payload': {
                        'filename': 'test.txt',
                        'size': 17,
                        'content_type': 'text/plain',
                    },
                },
            ),
        },
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    get_event_emitter_mock.assert_called_once_with()
    mock_request_events_now.assert_called_once_with()
    mock_upload_use_case_execute.assert_awaited_once_with(
        UploadFileCommand(
            file_stream=ANY,
            filename='test.txt',
            content_type='text/plain',
            size=17,
            user_id=1,
            account_id=1,
        ),
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()
