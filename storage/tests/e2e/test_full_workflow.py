from unittest.mock import MagicMock

import pytest

from ..fixtures.e2e import AsyncIteratorMock


class TestCompleteUploadDownloadWorkflow:
    """Test complete upload and download workflow"""

    def test_workflow__basic_upload_download__return_success_responses(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        sample_file_content,
        auth_headers,
        mock_upload_response,
        mock_download_response,
        mock_upload_use_case_execute,
        mock_download_use_case_execute,
    ):
        """Test basic upload and download workflow"""
        # Arrange
        filename = 'workflow_test.txt'
        content_type = 'text/plain'

        # Mock upload use case
        mock_upload_use_case_execute.return_value = mock_upload_response

        # Mock download use case
        mock_download_use_case_execute.return_value = mock_download_response

        # Act - Upload
        upload_response = e2e_client.post(
            '/upload',
            files={'file': (filename, sample_file_content, content_type)},
            headers=auth_headers,
        )

        # Assert - Upload
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert 'file_id' in upload_data
        assert 'public_url' in upload_data
        assert upload_data['file_id'] == 'test-file-id-123'

        file_id = upload_data['file_id']

        # Act - Download
        download_response = e2e_client.get(f'/{file_id}', headers=auth_headers)

        # Assert - Download
        assert download_response.status_code == 200
        assert 'text/plain' in download_response.headers['content-type']
        assert 'content-disposition' in download_response.headers

    @pytest.mark.parametrize(
        'filename,content,content_type',
        [
            ('text.txt', b'This is a text file', 'text/plain'),
            ('image.jpg', b'fake-jpeg-data', 'image/jpeg'),
            ('document.pdf', b'fake-pdf-data', 'application/pdf'),
            ('data.json', b'{"key": "value"}', 'application/json'),
            ('script.py', b'print("hello")', 'text/x-python'),
        ],
    )
    def test_workflow__different_file_types__return_success_responses(
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
        mock_download_use_case_execute,
    ):
        """Test workflow with different file types"""
        # Mock upload
        mock_response = MagicMock()
        mock_response.file_id = f'test-file-id-{filename}'
        mock_response.public_url = (
            f'http://localhost:8000/test-file-id-{filename}'
        )
        mock_upload_use_case_execute.return_value = mock_response

        # Mock download
        mock_record = MagicMock()
        mock_record.file_id = f'test-file-id-{filename}'
        mock_record.filename = filename
        mock_record.content_type = content_type
        mock_record.size = len(content)
        mock_download_use_case_execute.return_value = (
            mock_record,
            AsyncIteratorMock(content),
        )

        # Act - Upload
        upload_response = e2e_client.post(
            '/upload',
            files={'file': (filename, content, content_type)},
            headers=auth_headers,
        )

        # Assert - Upload
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert 'file_id' in upload_data
        assert 'public_url' in upload_data

        file_id = upload_data['file_id']

        # Act - Download
        download_response = e2e_client.get(f'/{file_id}', headers=auth_headers)

        # Assert - Download
        assert download_response.status_code == 200
        assert content_type in download_response.headers['content-type']
        assert 'content-disposition' in download_response.headers
