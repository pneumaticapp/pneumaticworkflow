"""Tests for the records the endpoints write into the audit journal."""

from datetime import UTC, datetime
from unittest.mock import ANY

from src.domain.entities.file_record import FileRecord
from src.shared_kernel.events.schema import EventName
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
    HttpTimeoutError,
)
from tests.fixtures.unit import (
    API_FILE_ID as FILE_ID,
    CapturingEmitter,
)


def test_upload__ok__upload_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_response,
    mock_upload_use_case_execute,
    mock_events_file_upload,
):
    # arrange
    mock_upload_use_case_execute.return_value = mock_upload_response
    journaled = []

    async def journal(**kwargs):
        journaled.append(kwargs)

    mock_events_file_upload.side_effect = journal

    # act
    response = e2e_client.post(
        '/upload',
        files={'file': ('test.txt', sample_file_content, 'text/plain')},
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    mock_events_file_upload.assert_awaited_once_with(
        user=ANY,
        file_id=mock_upload_response.file_id,
        file=ANY,
    )
    assert len(journaled) == 1
    assert journaled[0]['user'].user_id == 1
    assert journaled[0]['file'].filename == 'test.txt'
    assert journaled[0]['file'].content_type == 'text/plain'
    assert journaled[0]['file'].size == len(sample_file_content)


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


def test_download__owner_whole_file__download_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_response,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    file_record, stream = mock_download_response
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = stream

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


def test_download__range_from_first_byte__download_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
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


def test_download__range_past_first_byte__same_download_not_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
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


def test_download__range_not_satisfiable__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
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


def test_download__non_owner_granted__download_journaled_as_not_owner(
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
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='report.pdf',
        content_type='application/pdf',
        size=10,
        user_id=2,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
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


def test_download__non_owner_denied__refusal_journaled(
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
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='report.pdf',
        content_type='application/pdf',
        size=10,
        user_id=2,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
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
    mock_download_use_case_get_stream.assert_not_awaited()


def test_download__permission_check_timed_out__nothing_journaled(
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
    file_record = FileRecord(
        file_id=FILE_ID,
        filename='report.pdf',
        content_type='application/pdf',
        size=10,
        user_id=2,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
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
    mock_download_use_case_get_stream.assert_not_awaited()


def test_download__stream_failed_to_open__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_response,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_events_file_download,
):
    # arrange
    file_record, _stream = mock_download_response
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


def test_download__not_found__nothing_journaled(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_events_file_download,
    mock_events_file_access_denied,
):
    # arrange
    mock_download_use_case_get_metadata.side_effect = DomainFileNotFoundError(
        file_id=FILE_ID
    )

    # act
    response = e2e_client.get(f'/{FILE_ID}', headers=auth_headers)

    # assert
    assert response.status_code == 404
    mock_events_file_download.assert_not_awaited()
    mock_events_file_access_denied.assert_not_awaited()
    mock_http_client.assert_not_awaited()


def test_download__real_records__context_of_the_response(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_response,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mocker,
):
    """The record carries the id the caller got back in X-Request-ID
    and the address of the caller: the one property the middleware
    order in main.py exists for, checked through the real stack."""

    # arrange
    file_record, stream = mock_download_response
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = stream
    emitter = CapturingEmitter()
    mocker.patch(
        'src.shared_kernel.events.request_events.get_event_emitter',
        return_value=emitter,
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
    assert len(emitter.events) == 1
    event = emitter.events[0]
    assert event.type == EventName.FILE_DOWNLOAD
    assert event.context.request_id == response.headers['x-request-id']
    assert event.context.ip == '203.0.113.7'
    assert event.context.user_agent == 'Reader/1.0'
    assert event.payload['is_owner'] is True
