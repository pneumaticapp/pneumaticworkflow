from unittest.mock import AsyncMock

import pytest
from src.infra.repositories.storage_service import StorageService


class TestStorageService:
    """Test StorageService"""

    def test_get_storage_path__valid_account__return_bucket_and_path(self):
        """Test storage path generation"""
        # Arrange
        service = StorageService()

        # Act
        bucket_name, file_path = service.get_storage_path(
            account_id=1,
            file_id='test-file-id',
        )

        # Assert
        assert '1' in bucket_name
        assert file_path == 'test-file-id'

    @pytest.mark.asyncio
    async def test_upload_file__valid_data__upload_successfully(
        self,
        mock_aioboto3_session,
    ):
        """Test successful file upload"""
        # Arrange
        service = StorageService()
        bucket_name = 'test-bucket'
        file_path = 'test-file.txt'
        file_content = b'test content'
        content_type = 'text/plain'

        mock_s3_client = AsyncMock()
        (
            mock_aioboto3_session.return_value.client.return_value.__aenter__
        ).return_value = mock_s3_client

        # Act
        await service.upload_file(
            bucket_name,
            file_path,
            file_content,
            content_type,
        )

        # Assert
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file__valid_file__return_content_generator(
        self,
        mock_aioboto3_session,
    ):
        """Test successful file download"""
        # Arrange
        service = StorageService()
        bucket_name = 'test-bucket'
        file_path = 'test-file.txt'

        mock_s3_client = AsyncMock()

        # Create mock for async generator
        async def mock_iter_chunks(chunk_size=None):
            yield b'test content'

        mock_body = AsyncMock()
        mock_body.iter_chunks = mock_iter_chunks

        mock_s3_client.get_object.return_value = {'Body': mock_body}
        (
            mock_aioboto3_session.return_value.client.return_value.__aenter__
        ).return_value = mock_s3_client

        # Act
        content_generator = service.download_file(bucket_name, file_path)

        # Assert
        content = b''
        async for chunk in content_generator:
            content += chunk

        assert content == b'test content'
        mock_s3_client.get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file__chunked_content__return_all_chunks(
        self,
        mock_aioboto3_session,
    ):
        """Test chunked file download"""
        # Arrange
        service = StorageService()
        bucket_name = 'test-bucket'
        file_path = 'large-file.txt'

        mock_s3_client = AsyncMock()

        # Create mock for async generator with multiple chunks
        async def mock_iter_chunks(chunk_size=None):
            yield b'chunk1'
            yield b'chunk2'

        mock_body = AsyncMock()
        mock_body.iter_chunks = mock_iter_chunks

        mock_s3_client.get_object.return_value = {'Body': mock_body}
        (
            mock_aioboto3_session.return_value.client.return_value.__aenter__
        ).return_value = mock_s3_client

        # Act
        content_generator = service.download_file(bucket_name, file_path)

        # Assert
        chunks = []
        async for chunk in content_generator:
            chunks.append(chunk)

        assert chunks == [b'chunk1', b'chunk2']
        mock_s3_client.get_object.assert_called_once()
