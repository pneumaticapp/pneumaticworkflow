"""Tests for the records the download endpoint writes into the journal."""

import json
from unittest.mock import ANY, AsyncMock

import jwt

from src.application.dto import DownloadFileQuery
from src.shared_kernel.config import get_settings
from src.shared_kernel.events.schema import EventName
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
    HttpTimeoutError,
)
from tests.fixtures.unit import (
    API_FILE_ID as FILE_ID,
    EMITTER_MAXLEN,
    EMITTER_STREAM_KEY,
)


def test_download__owner_whole_file__download_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    file_record = make_file_record()
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 10])

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 200
    mock_events_file_download.assert_awaited_once_with(
        user=ANY,
        file_record=file_record,
        is_owner=True,
    )
    mock_events_file_access_denied.assert_not_awaited()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header=None,
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__range_from_first_byte__download_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = make_file_record(
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
    )
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 100])

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={**auth_headers, 'Range': 'bytes=0-99'},
    )

    # assert
    assert response.status_code == 206
    mock_events_file_download.assert_awaited_once_with(
        user=ANY,
        file_record=file_record,
        is_owner=True,
    )
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(
            file_id=FILE_ID,
            user_id=1,
            range_header='bytes=0-99',
        ),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header='bytes=0-99',
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__range_past_first_byte__same_download_not_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = make_file_record(
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
    )
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 100])

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={**auth_headers, 'Range': 'bytes=100-199'},
    )

    # assert
    assert response.status_code == 206

    # The ranges that follow the one opening a download are the same
    # download. The accepted cost: a client that never asks for byte
    # zero leaves no record at all.
    mock_events_file_download.assert_not_awaited()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(
            file_id=FILE_ID,
            user_id=1,
            range_header='bytes=100-199',
        ),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header='bytes=100-199',
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__malformed_range__download_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    """A Range the service cannot read is served as the whole file,
    so it is journaled as a download from the first byte."""

    # arrange
    file_record = make_file_record()
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 10])

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={**auth_headers, 'Range': 'items=5-9'},
    )

    # assert
    assert response.status_code == 200
    mock_events_file_download.assert_awaited_once_with(
        user=ANY,
        file_record=file_record,
        is_owner=True,
    )
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(
            file_id=FILE_ID,
            user_id=1,
            range_header='items=5-9',
        ),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header='items=5-9',
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__range_not_satisfiable__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = make_file_record(
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
    )
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b''])

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={**auth_headers, 'Range': 'bytes=5000-'},
    )

    # assert
    assert response.status_code == 416
    mock_events_file_download.assert_not_awaited()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(
            file_id=FILE_ID,
            user_id=1,
            range_header='bytes=5000-',
        ),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header='bytes=5000-',
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__non_owner_granted__download_journaled_as_not_owner(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    file_record = make_file_record(user_id=2)
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 10])
    mock_http_client.return_value = True

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 200
    mock_http_client.assert_awaited_once_with(user=ANY, file_id=FILE_ID)
    mock_events_file_download.assert_awaited_once_with(
        user=ANY,
        file_record=file_record,
        is_owner=False,
    )
    mock_events_file_access_denied.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header=None,
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__non_owner_denied__refusal_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    file_record = make_file_record(user_id=2)
    mock_download_use_case_get_metadata.return_value = file_record
    mock_http_client.return_value = False

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 403
    mock_http_client.assert_awaited_once_with(user=ANY, file_id=FILE_ID)
    mock_events_file_access_denied.assert_awaited_once_with(
        user=ANY,
        file_record=file_record,
    )
    mock_events_file_download.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_not_awaited()
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__permission_check_timed_out__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    file_record = make_file_record(user_id=2)
    mock_download_use_case_get_metadata.return_value = file_record
    mock_http_client.side_effect = HttpTimeoutError(
        url='http://backend/attachments/check-permission',
        timeout=10.0,
    )

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 504
    mock_http_client.assert_awaited_once_with(user=ANY, file_id=FILE_ID)
    mock_events_file_access_denied.assert_not_awaited()
    mock_events_file_download.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_not_awaited()
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__stream_failed_to_open__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = make_file_record()
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.side_effect = DomainFileNotFoundError(
        file_id=FILE_ID,
    )

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 404
    mock_events_file_download.assert_not_awaited()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header=None,
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__not_found__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    mock_download_use_case_get_metadata.side_effect = DomainFileNotFoundError(
        file_id=FILE_ID,
    )

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 404
    mock_events_file_download.assert_not_awaited()
    mock_events_file_access_denied.assert_not_awaited()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_not_awaited()
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__guest_token_own_file__journaled_as_owner(
    e2e_client,
    mock_http_client,
    mock_storage_service,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    """A guest token has no user: a file uploaded under a token of the
    same account is its own, and no permission check is asked for."""

    # arrange
    guest_token = jwt.encode(
        payload={'user_id': None, 'account_id': 1},
        key=get_settings().DJANGO_SECRET_KEY,
        algorithm='HS256',
    )
    file_record = make_file_record(user_id=None)
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 10])

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={'X-Guest-Authorization': guest_token},
    )

    # assert
    assert response.status_code == 200
    mock_events_file_download.assert_awaited_once_with(
        user=ANY,
        file_record=file_record,
        is_owner=True,
    )
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=None, range_header=None),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header=None,
    )
    mock_storage_service.assert_not_called()


def test_download__events_stream_unavailable__file_served(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    events_emitter,
    mock_events_redis_from_url,
    mock_request_events_now,
    mocker,
):
    # arrange
    file_record = make_file_record()
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 10])
    client_mock = AsyncMock()
    client_mock.xadd.side_effect = ConnectionError('refused')
    mock_events_redis_from_url.return_value = client_mock
    get_event_emitter_mock = mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=events_emitter,
    )

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={**auth_headers, 'X-Request-ID': 'req-1'},
    )

    # assert
    assert response.status_code == 200
    assert response.content == b'x' * 10
    client_mock.xadd.assert_awaited_once_with(
        name=EMITTER_STREAM_KEY,
        fields={
            'type': 'file.download',
            'data': json.dumps(
                {
                    'type': 'file.download',
                    'category': 'files',
                    'service': 'pneumatic-file-service',
                    'ts': '2026-09-09T12:00:00.000123Z',
                    'account_id': 1,
                    'actor': {'id': 1, 'email': None, 'user_type': 'user'},
                    'auth_type': 'User',
                    'object': {'type': 'file', 'id': FILE_ID},
                    'workflow_id': None,
                    'task_id': None,
                    'ip': 'testclient',
                    'user_agent': 'testclient',
                    'request_id': 'req-1',
                    'payload': {
                        'filename': 'report.pdf',
                        'size': 10,
                        'content_type': 'application/pdf',
                        'is_owner': True,
                    },
                },
            ),
        },
        maxlen=EMITTER_MAXLEN,
        approximate=True,
    )
    get_event_emitter_mock.assert_called_once_with()
    mock_request_events_now.assert_called_once_with()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header=None,
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()


def test_download__real_records__context_of_the_response(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    make_file_record,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    capturing_emitter,
    mocker,
):
    """The record carries the id the caller got back in X-Request-ID
    and the address of the caller: the one property the middleware
    order in main.py exists for, checked through the real stack."""

    # arrange
    file_record = make_file_record()
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = iter([b'x' * 10])
    get_event_emitter_mock = mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=capturing_emitter,
    )

    # act
    response = e2e_client.get(
        f'/{FILE_ID}',
        headers={
            **auth_headers,
            'X-Real-IP': '203.0.113.7',
            'User-Agent': 'Reader/1.0',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(capturing_emitter.events) == 1
    event = capturing_emitter.events[0]
    assert event.type == EventName.FILE_DOWNLOAD
    assert event.context.request_id == response.headers['x-request-id']
    assert event.context.ip == '203.0.113.7'
    assert event.context.user_agent == 'Reader/1.0'
    assert event.payload['is_owner'] is True
    get_event_emitter_mock.assert_called_once_with()
    mock_http_client.assert_not_awaited()
    mock_download_use_case_get_metadata.assert_awaited_once_with(
        DownloadFileQuery(file_id=FILE_ID, user_id=1, range_header=None),
    )
    mock_download_use_case_get_stream.assert_awaited_once_with(
        file_record=file_record,
        range_header=None,
    )
    mock_auth_middleware.assert_awaited_once_with('valid-token')
    mock_storage_service.assert_not_called()
