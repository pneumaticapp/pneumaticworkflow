"""Tests for API endpoints."""

from datetime import UTC, datetime
from unittest.mock import ANY, MagicMock

import pytest

from src.domain.entities.file_record import FileRecord
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
)


def test_upload__valid_file_with_auth__return_ok(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    sample_file_content,
    auth_headers,
    mock_upload_response,
    mock_upload_use_case_execute,
):
    # arrange
    mock_upload_use_case_execute.return_value = mock_upload_response

    # act
    response = e2e_client.post(
        '/upload',
        files={
            'file': (
                'test.txt',
                sample_file_content,
                'text/plain',
            ),
        },
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    assert 'public_url' in data
    assert 'file_id' in data


def test_upload__no_auth__return_401(e2e_client):
    # act
    response = e2e_client.post(
        '/upload',
        files={
            'file': (
                'test.txt',
                b'test file content',
                'text/plain',
            ),
        },
    )

    # assert
    assert response.status_code == 401


def test_upload__no_file__return_401(e2e_client):
    # act
    response = e2e_client.post('/upload')

    # assert
    assert response.status_code == 401


def test_upload__no_file_with_auth__return_422(
    e2e_client,
    mock_auth_middleware,
    auth_headers,
):
    # act
    response = e2e_client.post(
        '/upload',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 422


def test_upload__large_file__return_ok(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    sample_large_file_content,
    auth_headers,
    mock_upload_use_case_execute,
):
    # arrange
    mock_upload_use_case_execute.return_value = MagicMock(
        file_id='87654321-4321-8765-4321-876543210987',
        public_url=(
            'http://localhost:8000/download/'
            '87654321-4321-8765-4321-876543210987'
        ),
    )

    # act
    response = e2e_client.post(
        '/upload',
        files={
            'file': (
                'large.txt',
                sample_large_file_content,
                'text/plain',
            ),
        },
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    assert 'public_url' in data
    assert 'file_id' in data
    assert data['file_id'] == ('87654321-4321-8765-4321-876543210987')


def test_download__valid_file__return_content(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_response,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    file_record, stream = mock_download_response
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = stream

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    assert 'text/plain' in response.headers['content-type']
    assert (
        response.headers['content-disposition']
        == "attachment; filename*=utf-8''test_file.txt"
    )
    assert response.headers['accept-ranges'] == 'bytes'


def test_download__range_header__return_206(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def partial_stream():
        yield b'partial'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = partial_stream()

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers={
            **auth_headers,
            'Range': 'bytes=0-99',
        },
    )

    # assert
    assert response.status_code == 206
    assert response.headers['content-range'] == ('bytes 0-99/1000')
    assert response.headers['content-length'] == '100'
    assert response.headers['accept-ranges'] == 'bytes'


def test_download__range_header_exceeds_size__return_capped(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='video.mp4',
        content_type='video/mp4',
        size=100,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def partial_stream():
        yield b'partial'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = partial_stream()

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers={
            **auth_headers,
            'Range': 'bytes=0-99999',
        },
    )

    # assert
    assert response.status_code == 206
    assert response.headers['content-range'] == 'bytes 0-99/100'
    assert response.headers['content-length'] == '100'
    assert response.headers['accept-ranges'] == 'bytes'


def test_download__invalid_range_header__return_416(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='video.mp4',
        content_type='video/mp4',
        size=1000,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def partial_stream():
        yield b'partial'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = partial_stream()

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers={
            **auth_headers,
            'Range': 'bytes=1000-1005',
        },
    )

    # assert
    assert response.status_code == 416
    assert response.headers['content-range'] == 'bytes */1000'


def test_download__no_auth__return_401(e2e_client):
    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
    )

    # assert
    assert response.status_code == 401


def test_download__not_found__return_404(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    auth_headers,
    mock_download_use_case_get_metadata,
):
    # arrange
    mock_download_use_case_get_metadata.side_effect = DomainFileNotFoundError(
        file_id=('00000000-0000-0000-0000-000000000000'),
    )

    # act
    response = e2e_client.get(
        '/00000000-0000-0000-0000-000000000000',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 404


def test_download__no_permission__return_403(
    e2e_client,
    mock_auth_middleware,
    auth_headers,
    mock_http_client_check_permission,
    mock_download_use_case_get_metadata,
):
    # arrange
    file_record = MagicMock()
    file_record.file_id = '12345678-1234-5678-1234-567812345678'
    file_record.filename = 'test_file.txt'
    file_record.content_type = 'text/plain'
    file_record.size = 12
    file_record.user_id = 999
    file_record.account_id = 1
    mock_download_use_case_get_metadata.return_value = file_record
    mock_http_client_check_permission.return_value = False

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 403


def test_download__owner_access__return_content(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_response,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    file_record, stream = mock_download_response
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = stream
    mock_http_client.check_file_permission.return_value = False

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    mock_download_use_case_get_metadata.assert_called_once_with(ANY)
    mock_download_use_case_get_stream.assert_called_once_with(
        file_record=ANY,
        range_header=ANY,
    )
    mock_http_client.check_file_permission.assert_not_called()


def test_download__non_owner_no_perm__return_403(
    e2e_client,
    mock_auth_middleware,
    mock_http_client_check_permission,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='test_file.txt',
        content_type='text/plain',
        size=12,
        user_id=999,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    mock_download_use_case_get_metadata.return_value = file_record
    mock_http_client_check_permission.return_value = False

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 403
    mock_download_use_case_get_metadata.assert_called_once_with(ANY)
    mock_download_use_case_get_stream.assert_not_called()
    mock_http_client_check_permission.assert_called_once_with(
        user=ANY,
        file_id=ANY,
    )


@pytest.mark.parametrize(
    ('filename', 'content', 'content_type'),
    [
        ('text.txt', b'Text file', 'text/plain'),
        ('image.jpg', b'fake-jpeg', 'image/jpeg'),
        ('doc.pdf', b'fake-pdf', 'application/pdf'),
        ('data.json', b'{"k": "v"}', 'application/json'),
        ('script.py', b'print("hi")', 'text/x-python'),
    ],
)
def test_upload__diff_content_types__return_ok(
    filename,
    content,
    content_type,
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_upload_use_case_execute,
):
    # arrange
    mock_upload_use_case_execute.return_value = MagicMock(
        file_id=('12345678-1234-5678-1234-567812345678'),
        public_url=(
            'http://localhost:8000/download/'
            '12345678-1234-5678-1234-567812345678'
        ),
    )

    # act
    response = e2e_client.post(
        '/upload',
        files={
            'file': (filename, content, content_type),
        },
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    assert 'public_url' in data
    assert 'file_id' in data


# --- Error body contract tests (backend-compatible format) ---


def test_upload__no_auth__error_body_format(e2e_client):
    """401 response body must use unified format."""
    # act
    response = e2e_client.post(
        '/upload',
        files={
            'file': (
                'test.txt',
                b'test file content',
                'text/plain',
            ),
        },
    )

    # assert
    assert response.status_code == 401
    data = response.json()
    assert 'code' in data
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_upload__no_file_with_auth__error_body_format(
    e2e_client,
    mock_auth_middleware,
    auth_headers,
):
    """422 response body must use unified format."""
    # act
    response = e2e_client.post(
        '/upload',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 422
    data = response.json()
    assert 'code' in data
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_download__not_found__error_body_format(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    auth_headers,
    mock_download_use_case_get_metadata,
):
    """404 response body must contain code=FILE_001 in unified format."""
    # arrange
    mock_download_use_case_get_metadata.side_effect = DomainFileNotFoundError(
        file_id='00000000-0000-0000-0000-000000000000',
    )

    # act
    response = e2e_client.get(
        '/00000000-0000-0000-0000-000000000000',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 404
    data = response.json()
    assert data['code'] == 'FILE_001'
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_download__no_permission__error_body_format(
    e2e_client,
    mock_auth_middleware,
    auth_headers,
    mock_http_client_check_permission,
    mock_download_use_case_get_metadata,
):
    """403 response body must use unified format."""
    # arrange
    file_record = MagicMock()
    file_record.file_id = '12345678-1234-5678-1234-567812345678'
    file_record.filename = 'test_file.txt'
    file_record.content_type = 'text/plain'
    file_record.size = 12
    file_record.user_id = 999
    file_record.account_id = 1
    mock_download_use_case_get_metadata.return_value = file_record
    mock_http_client_check_permission.return_value = False

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 403
    data = response.json()
    assert 'code' in data
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data


def test_download__no_auth__error_body_format(e2e_client):
    """401 on download must use unified format."""
    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
    )

    # assert
    assert response.status_code == 401
    data = response.json()
    assert 'code' in data
    assert 'message' in data
    assert 'error_type' not in data
    assert 'timestamp' not in data
    assert 'request_id' not in data


def test_error_body__allowed_keys_only(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    auth_headers,
    mock_download_use_case_get_metadata,
):
    """Error response must only contain {code, message, details}."""
    # arrange
    mock_download_use_case_get_metadata.side_effect = DomainFileNotFoundError(
        file_id='00000000-0000-0000-0000-000000000000',
    )

    # act
    response = e2e_client.get(
        '/00000000-0000-0000-0000-000000000000',
        headers=auth_headers,
    )

    # assert
    data = response.json()
    allowed_keys = {'code', 'message', 'details'}
    assert set(data.keys()).issubset(allowed_keys)


def test_download__legacy_gcs_file_id__return_content(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    """Legacy GCS file_id (non-UUID string) must be accepted."""
    # arrange
    legacy_file_id = 'VumcsgTMmIiSagrYrvDdMFUBbWhUYN_pic.png'
    file_record = FileRecord(
        file_id=legacy_file_id,
        filename='pic.png',
        content_type='image/png',
        size=2048,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def file_stream():
        yield b'fake-png-content'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = file_stream()

    # act
    response = e2e_client.get(
        f'/{legacy_file_id}',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    mock_download_use_case_get_metadata.assert_called_once()


def test_download__uuid_file_id__return_content(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    """New UUID-based file_id must still work."""
    # arrange
    uuid_file_id = '550e8400-e29b-41d4-a716-446655440000'
    file_record = FileRecord(
        file_id=uuid_file_id,
        filename='document.pdf',
        content_type='application/pdf',
        size=4096,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def file_stream():
        yield b'fake-pdf-content'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = file_stream()

    # act
    response = e2e_client.get(
        f'/{uuid_file_id}',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    mock_download_use_case_get_metadata.assert_called_once()


def test_download__legacy_file_id_with_dots__return_content(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    """Legacy file_id containing dots must be accepted."""
    # arrange
    legacy_file_id = 'ZfcsxZayjl9XST5mA0zdpqZ2zomLGM_report.final.v2.pdf'
    file_record = FileRecord(
        file_id=legacy_file_id,
        filename='report.final.v2.pdf',
        content_type='application/pdf',
        size=8192,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def file_stream():
        yield b'fake-pdf'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = file_stream()

    # act
    response = e2e_client.get(
        f'/{legacy_file_id}',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200


def test_error_body__details_is_dict_when_present(
    e2e_client,
    mock_auth_middleware,
    auth_headers,
):
    """When details exist in error, they must be {reason: str}."""
    # act
    response = e2e_client.post(
        '/upload',
        headers=auth_headers,
    )

    # assert
    data = response.json()
    if 'details' in data:
        assert isinstance(data['details'], dict)
        assert 'reason' in data['details']


# --- P0: Legacy file_id acceptance (extended) ---


@pytest.mark.parametrize(
    ('file_id', 'description'),
    [
        (
            '550e8400-e29b-41d4-a716-446655440000',
            'standard UUID',
        ),
        (
            'VumcsgTMmIiSagrYrvDdMFUBbWhUYN_pic.png',
            'legacy GCS key with extension',
        ),
        (
            'AbCdEfGh',
            'minimal 8-char file_id',
        ),
        (
            'a' * 64,
            'long 64-char file_id',
        ),
        (
            'file-with-dashes_and_underscores.tar.gz',
            'file_id with multiple dots and mixed separators',
        ),
    ],
)
def test_download__various_file_id_formats__accepted(
    file_id,
    description,
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    """Download route must accept various file_id formats."""
    # arrange
    file_record = FileRecord(
        file_id=file_id,
        filename='test.bin',
        content_type='application/octet-stream',
        size=100,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def file_stream():
        yield b'content'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = file_stream()

    # act
    response = e2e_client.get(
        f'/{file_id}',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200, f'Failed for {description}: {file_id}'


def test_download__url_encoded_legacy_id__decoded_by_fastapi(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    """URL-encoded file_id in path must be decoded by FastAPI."""
    # arrange
    decoded_id = 'NiihssB_Screencast 2023.webm'
    encoded_path = 'NiihssB_Screencast%202023.webm'
    file_record = FileRecord(
        file_id=decoded_id,
        filename='Screencast 2023.webm',
        content_type='video/webm',
        size=5000,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )

    async def file_stream():
        yield b'video-content'

    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = file_stream()

    # act
    response = e2e_client.get(
        f'/{encoded_path}',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    call_args = mock_download_use_case_get_metadata.call_args
    query = call_args[0][0]
    assert query.file_id == decoded_id


def test_download__legacy_id__permission_check_receives_string(
    e2e_client,
    mock_auth_middleware,
    auth_headers,
    mock_http_client_check_permission,
    mock_download_use_case_get_metadata,
):
    """Permission check must receive file_id as string, not UUID."""
    # arrange
    legacy_id = 'VumcsgTMmIiSagrYrvDd_report.pdf'
    file_record = MagicMock()
    file_record.file_id = legacy_id
    file_record.filename = 'report.pdf'
    file_record.content_type = 'application/pdf'
    file_record.size = 1024
    file_record.user_id = 999
    file_record.account_id = 1
    mock_download_use_case_get_metadata.return_value = file_record
    mock_http_client_check_permission.return_value = False

    # act
    response = e2e_client.get(
        f'/{legacy_id}',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 403
    mock_http_client_check_permission.assert_called_once()
    call_kwargs = mock_http_client_check_permission.call_args
    assert isinstance(call_kwargs.kwargs['file_id'], str)
    assert call_kwargs.kwargs['file_id'] == legacy_id
