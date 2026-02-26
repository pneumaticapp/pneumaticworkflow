from unittest.mock import MagicMock
from datetime import datetime, timezone
import pytest

from src.shared_kernel.exceptions import DomainFileNotFoundError
from src.domain.entities.file_record import FileRecord


class TestAPIEndpoints:
    """Test API endpoints."""

    def test_upload_endpoint__valid_file_with_auth__return_success_response(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        sample_file_content,
        auth_headers,
        mock_upload_response,
        mock_upload_use_case_execute,
    ):
        """Test successful file upload endpoint."""
        # Arrange
        mock_upload_use_case_execute.return_value = mock_upload_response

        # Act
        response = e2e_client.post(
            '/upload',
            files={'file': ('test.txt', sample_file_content, 'text/plain')},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'public_url' in data
        assert 'file_id' in data

    def test_upload_endpoint__no_auth__return_401(self, e2e_client):
        """Test upload endpoint without authentication."""
        # Arrange
        file_content = b'test file content'

        # Act
        response = e2e_client.post(
            '/upload',
            files={'file': ('test.txt', file_content, 'text/plain')},
        )

        # Assert
        assert response.status_code == 401

    def test_upload_endpoint__no_file__return_401(self, e2e_client):
        """Test upload endpoint without file."""
        # Act
        response = e2e_client.post('/upload')

        # Assert
        # Without authentication we get 401 from middleware
        assert response.status_code == 401

    def test_upload_endpoint__no_file_with_auth__return_422(
        self,
        e2e_client,
        mock_auth_middleware,
        auth_headers,
    ):
        """Test upload endpoint without file but with authentication."""
        # Act
        response = e2e_client.post('/upload', headers=auth_headers)

        # Assert
        # With authentication but no file - middleware passes request,
        # but FastAPI returns 422 due to missing file parameter
        assert response.status_code == 422

    def test_upload_endpoint__large_file__return_success_response(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        sample_large_file_content,
        auth_headers,
        mock_upload_use_case_execute,
    ):
        """Test upload endpoint with large file."""
        # Arrange
        mock_upload_use_case_execute.return_value = MagicMock(
            file_id='large-file-id',
            public_url='http://localhost:8000/download/large-file-id',
        )

        # Act
        response = e2e_client.post(
            '/upload',
            files={
                'file': ('large.txt', sample_large_file_content, 'text/plain'),
            },
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'public_url' in data
        assert 'file_id' in data
        assert data['file_id'] == 'large-file-id'

    def test_download_endpoint__valid_file_with_auth__return_file_content(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        auth_headers,
        mock_download_response,
        mock_download_use_case_get_metadata,
        mock_download_use_case_get_stream,
    ):
        """Test successful file download endpoint."""
        # Arrange
        file_record, stream = mock_download_response
        mock_download_use_case_get_metadata.return_value = file_record
        mock_download_use_case_get_stream.return_value = stream

        # Act
        response = e2e_client.get('/test-file-id', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert 'text/plain' in response.headers['content-type']
        assert response.headers['content-disposition'] == (
            'attachment; filename="test_file.txt"'
        )

    def test_download_endpoint__no_auth__return_401(self, e2e_client):
        """Test download endpoint without authentication."""
        # Act
        response = e2e_client.get('/test-file-id')

        # Assert
        assert response.status_code == 401

    def test_download_endpoint__file_not_found__return_404(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        auth_headers,
        mock_download_use_case_get_metadata,
    ):
        """Test download nonexistent file endpoint."""
        # Arrange
        mock_download_use_case_get_metadata.side_effect = (
            DomainFileNotFoundError('nonexistent-file-id')
        )

        # Act
        response = e2e_client.get('/nonexistent-file-id', headers=auth_headers)

        # Assert
        # FileNotFoundError should be handled and return 404
        assert response.status_code == 404

    def test_download_endpoint__no_permission__return_403(
        self,
        e2e_client,
        mock_auth_middleware,
        auth_headers,
        mock_http_client_check_permission,
        mock_download_use_case_get_metadata,
    ):
        """Test download endpoint without permission."""
        # Arrange
        file_record = MagicMock()
        file_record.file_id = 'test-file-id'
        file_record.filename = 'test_file.txt'
        file_record.content_type = 'text/plain'
        file_record.size = 12
        file_record.user_id = 999  # Different user
        file_record.account_id = 1
        mock_download_use_case_get_metadata.return_value = file_record
        mock_http_client_check_permission.return_value = False

        # Act
        response = e2e_client.get('/test-file-id', headers=auth_headers)

        # Assert
        assert response.status_code == 403

    def test_download_endpoint__owner_access__return_file_content(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        auth_headers,
        mock_download_response,
        mock_download_use_case_get_metadata,
        mock_download_use_case_get_stream,
    ):
        """Owner has access even if permission check fails."""
        # Arrange
        file_record, _ = mock_download_response
        mock_download_use_case_get_metadata.return_value = file_record
        mock_download_use_case_get_stream.return_value = _
        mock_http_client.check_file_permission.return_value = False

        # Act
        response = e2e_client.get('/test-file-id', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        mock_download_use_case_get_metadata.assert_called_once()
        mock_download_use_case_get_stream.assert_called_once()
        mock_http_client.check_file_permission.assert_not_called()

    def test_download_endpoint__non_owner_no_permission__return_403(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client_check_permission,
        auth_headers,
        mock_download_use_case_get_metadata,
        mock_download_use_case_get_stream,
    ):
        """Test download endpoint - non-owner without permission gets 403."""
        # Arrange
        file_record = FileRecord(
            file_id='test-file-id',
            filename='test_file.txt',
            content_type='text/plain',
            size=12,
            user_id=999,
            account_id=1,
            created_at=datetime.now(timezone.utc),
        )
        mock_download_use_case_get_metadata.return_value = file_record
        mock_http_client_check_permission.return_value = False

        # Act
        response = e2e_client.get('/test-file-id', headers=auth_headers)

        # Assert
        assert response.status_code == 403
        mock_download_use_case_get_metadata.assert_called_once()
        mock_download_use_case_get_stream.assert_not_called()
        mock_http_client_check_permission.assert_called_once()

    @pytest.mark.parametrize(
        ('filename', 'content', 'content_type'),
        [
            ('text.txt', b'This is a text file', 'text/plain'),
            ('image.jpg', b'fake-jpeg-data', 'image/jpeg'),
            ('document.pdf', b'fake-pdf-data', 'application/pdf'),
            ('data.json', b'{"key": "value"}', 'application/json'),
            ('script.py', b'print("hello")', 'text/x-python'),
        ],
    )
    def test_upload_endpoint__different_content_types__success_responses(
        self,
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
        """Test upload endpoint with different content types."""
        # Arrange
        mock_upload_use_case_execute.return_value = MagicMock(
            file_id='test-file-id',
            public_url='http://localhost:8000/download/test-file-id',
        )

        # Act
        response = e2e_client.post(
            '/upload',
            files={'file': (filename, content, content_type)},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'public_url' in data
        assert 'file_id' in data
