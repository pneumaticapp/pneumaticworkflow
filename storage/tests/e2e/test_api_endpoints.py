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
    mock_upload_use_case_execute.return_value = (
        mock_upload_response
    )

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
        '/upload', headers=auth_headers,
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
    assert data['file_id'] == (
        '87654321-4321-8765-4321-876543210987'
    )


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
    mock_download_use_case_get_metadata.return_value = (
        file_record
    )
    mock_download_use_case_get_stream.return_value = (
        stream
    )

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    assert 'text/plain' in response.headers[
        'content-type'
    ]
    assert response.headers[
        'content-disposition'
    ] == "attachment; filename*=utf-8''test_file.txt"
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

    mock_download_use_case_get_metadata.return_value = (
        file_record
    )
    mock_download_use_case_get_stream.return_value = (
        partial_stream()
    )

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers={
            **auth_headers, 'Range': 'bytes=0-99',
        },
    )

    # assert
    assert response.status_code == 206
    assert response.headers['content-range'] == (
        'bytes 0-99/1000'
    )
    assert response.headers['content-length'] == '100'
    assert response.headers['accept-ranges'] == 'bytes'


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
    mock_download_use_case_get_metadata.side_effect = (
        DomainFileNotFoundError(
            file_id=(
                '00000000-0000-0000-0000-000000000000'
            ),
        )
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
    file_record.file_id = (
        '12345678-1234-5678-1234-567812345678'
    )
    file_record.filename = 'test_file.txt'
    file_record.content_type = 'text/plain'
    file_record.size = 12
    file_record.user_id = 999
    file_record.account_id = 1
    mock_download_use_case_get_metadata.return_value = (
        file_record
    )
    mock_http_client_check_permission.return_value = (
        False
    )

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
    mock_download_use_case_get_metadata.return_value = (
        file_record
    )
    mock_download_use_case_get_stream.return_value = (
        stream
    )
    mock_http_client.check_file_permission \
        .return_value = False

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 200
    mock_download_use_case_get_metadata \
        .assert_called_once_with(ANY)
    mock_download_use_case_get_stream \
        .assert_called_once_with(
            file_record=ANY, range_header=ANY,
        )
    mock_http_client.check_file_permission \
        .assert_not_called()


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
    mock_download_use_case_get_metadata.return_value = (
        file_record
    )
    mock_http_client_check_permission.return_value = (
        False
    )

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=auth_headers,
    )

    # assert
    assert response.status_code == 403
    mock_download_use_case_get_metadata \
        .assert_called_once_with(ANY)
    mock_download_use_case_get_stream \
        .assert_not_called()
    mock_http_client_check_permission \
        .assert_called_once_with(
            user=ANY, file_id=ANY,
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
    mock_upload_use_case_execute.return_value = (
        MagicMock(
            file_id=(
                '12345678-1234-5678-1234-567812345678'
            ),
            public_url=(
                'http://localhost:8000/download/'
                '12345678-1234-5678-1234-567812345678'
            ),
        )
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
