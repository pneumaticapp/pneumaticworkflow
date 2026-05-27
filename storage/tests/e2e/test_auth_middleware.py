from unittest.mock import MagicMock

from tests.fixtures.e2e import AsyncIteratorMock


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    def test_auth_check__valid_token__passes_authentication(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        mock_download_use_case_get_metadata,
        mock_download_use_case_get_stream,
    ):
        """Test valid token authentication."""
        # Arrange
        headers = {'Authorization': 'Bearer test-token'}
        file_record = MagicMock()
        file_record.file_id = '12345678-1234-5678-1234-567812345678'
        file_record.filename = 'test.txt'
        file_record.content_type = 'text/plain'
        file_record.size = 12
        file_record.user_id = 1  # Owner
        mock_download_use_case_get_metadata.return_value = file_record
        mock_download_use_case_get_stream.return_value = (
            AsyncIteratorMock(b'test content')
        )

        # Act
        response = e2e_client.get(
            '/12345678-1234-5678-1234-567812345678',
            headers=headers,
        )

        # Assert
        assert response.status_code != 401

    def test_auth_check__missing_token__return_401(self, e2e_client):
        """Test missing token authentication."""
        # Arrange
        # No headers

        # Act
        response = e2e_client.get('/12345678-1234-5678-1234-567812345678')

        # Assert
        assert response.status_code == 401

    def test_auth_check__valid_session_token__passes_authentication(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        mock_download_use_case_get_metadata,
        mock_download_use_case_get_stream,
    ):
        """Test valid session token authentication."""
        # Arrange
        cookies = {'token': 'valid-session-token'}
        file_record = MagicMock()
        file_record.file_id = '12345678-1234-5678-1234-567812345678'
        file_record.filename = 'test.txt'
        file_record.content_type = 'text/plain'
        file_record.size = 12
        file_record.user_id = 1  # Owner
        mock_download_use_case_get_metadata.return_value = file_record
        mock_download_use_case_get_stream.return_value = (
            AsyncIteratorMock(b'test content')
        )

        # Act
        response = e2e_client.get(
            '/12345678-1234-5678-1234-567812345678',
            cookies=cookies,
        )

        # Assert
        assert response.status_code != 401

    def test_auth_check__invalid_session_token__return_401(
        self,
        e2e_client,
        mock_redis_auth_client_get,
    ):
        """Test invalid session token authentication."""
        # Arrange
        cookies = {'token': 'invalid-session-token'}

        mock_redis_auth_client_get.return_value = None

        # Act
        response = e2e_client.get(
            '/12345678-1234-5678-1234-567812345678',
            cookies=cookies,
        )

        # Assert
        assert response.status_code == 401
