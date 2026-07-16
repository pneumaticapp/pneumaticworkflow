"""Tests for authentication middleware (e2e)."""

from unittest.mock import MagicMock

from tests.fixtures.e2e import AsyncIteratorMock


def test_auth__valid_token__passes(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    headers = {'Authorization': 'Bearer test-token'}
    file_record = MagicMock()
    file_record.file_id = '12345678-1234-5678-1234-567812345678'
    file_record.filename = 'test.txt'
    file_record.content_type = 'text/plain'
    file_record.size = 12
    file_record.user_id = 1
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = AsyncIteratorMock(
        b'test content'
    )

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        headers=headers,
    )

    # assert
    assert response.status_code != 401


def test_auth__missing_token__return_401(e2e_client):
    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
    )

    # assert
    assert response.status_code == 401


def test_auth__valid_session_token__passes(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    cookies = {'token': 'valid-session-token'}
    file_record = MagicMock()
    file_record.file_id = '12345678-1234-5678-1234-567812345678'
    file_record.filename = 'test.txt'
    file_record.content_type = 'text/plain'
    file_record.size = 12
    file_record.user_id = 1
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = AsyncIteratorMock(
        b'test content'
    )

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        cookies=cookies,
    )

    # assert
    assert response.status_code != 401


def test_auth__invalid_session__return_401(
    e2e_client,
    mock_redis_auth_client_get,
):
    # arrange
    cookies = {'token': 'invalid-session-token'}
    mock_redis_auth_client_get.return_value = None

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        cookies=cookies,
    )

    # assert
    assert response.status_code == 401


def test_auth__file_service_auth_cookie__passes(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    """Cookie set by Django FileServiceAuthMiddleware should authenticate."""
    # arrange
    cookies = {'file_service_auth': 'valid-django-token'}
    file_record = MagicMock()
    file_record.file_id = '12345678-1234-5678-1234-567812345678'
    file_record.filename = 'test.txt'
    file_record.content_type = 'text/plain'
    file_record.size = 12
    file_record.user_id = 1
    mock_download_use_case_get_metadata.return_value = file_record
    mock_download_use_case_get_stream.return_value = AsyncIteratorMock(
        b'test content'
    )

    # act
    response = e2e_client.get(
        '/12345678-1234-5678-1234-567812345678',
        cookies=cookies,
    )

    # assert
    assert response.status_code != 401
