from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from src.application.dto.file_dtos import (
    DownloadFileQuery,
    UploadFileCommand,
    UploadFileUseCaseResponse,
)
from src.application.use_cases.file_download import DownloadFileUseCase
from src.application.use_cases.file_upload import UploadFileUseCase
from src.domain.entities.file_record import FileRecord
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
    StorageError,
)


class TestUploadFileUseCase:
    """Test UploadFileUseCase."""

    @pytest.mark.asyncio
    async def test_upload_file__valid_command__return_response(
        self,
        mock_storage_service,
        mock_repository,
    ):
        """Test successful file upload."""
        # Arrange
        command = UploadFileCommand(
            file_content=b'test content',
            filename='test.txt',
            content_type='text/plain',
            size=12,
            user_id=1,
            account_id=1,
        )

        file_record = FileRecord(
            file_id='test-file-id',
            filename='test.txt',
            content_type='text/plain',
            size=12,
            user_id=1,
            account_id=1,
            created_at=datetime.now(),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_repository.create.return_value = file_record
        mock_storage_service.get_storage_path.return_value = (
            'test-bucket',
            'test-file-id',
        )
        mock_storage_service.upload_file.return_value = None

        use_case = UploadFileUseCase(
            file_repository=mock_repository,
            storage_service=mock_storage_service,
            unit_of_work=mock_uow,
            fastapi_base_url='http://localhost:8000',
        )

        # Act
        result = await use_case.execute(command)

        # Assert
        assert isinstance(result, UploadFileUseCaseResponse)
        assert result.file_id is not None
        assert result.public_url.startswith('http://localhost:8000/')
        assert result.file_id in result.public_url

        mock_repository.create.assert_called_once()
        mock_storage_service.upload_file.assert_called_once_with(
            bucket_name='test-bucket',
            file_path='test-file-id',
            file_content=b'test content',
            content_type='text/plain',
        )
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file__storage_error__raise_storage_error(
        self,
        mock_storage_service,
        mock_repository,
    ):
        """Test upload with storage error."""
        # Arrange
        command = UploadFileCommand(
            file_content=b'test content',
            filename='test.txt',
            content_type='text/plain',
            size=12,
            user_id=1,
            account_id=1,
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        mock_storage_service.get_storage_path.return_value = (
            'test-bucket',
            'test-file-id',
        )
        mock_storage_service.upload_file.side_effect = (
            StorageError.upload_failed('Upload failed')
        )

        use_case = UploadFileUseCase(
            file_repository=mock_repository,
            storage_service=mock_storage_service,
            unit_of_work=mock_uow,
            fastapi_base_url='http://localhost:8000',
        )

        # Act & Assert
        with pytest.raises(StorageError):
            await use_case.execute(command)


class TestDownloadFileUseCase:
    """Test DownloadFileUseCase."""

    @pytest.mark.asyncio
    async def test_download_file__valid_query__return_file_and_stream(
        self,
        mock_storage_service,
        mock_repository,
    ):
        """Test successful file download."""
        # Arrange
        query = DownloadFileQuery(file_id='test-file-id', user_id=1)

        file_record = FileRecord(
            file_id='test-file-id',
            filename='test.txt',
            content_type='text/plain',
            size=12,
            user_id=1,
            account_id=1,
            created_at=datetime.now(),
        )

        mock_repository.get_by_id.return_value = file_record
        mock_storage_service.get_storage_path.return_value = (
            'test-bucket',
            'test-file-id',
        )

        async def mock_download_generator():
            yield b'test content'

        mock_storage_service.download_file = Mock(
            return_value=mock_download_generator(),
        )

        use_case = DownloadFileUseCase(
            file_repository=mock_repository,
            storage_service=mock_storage_service,
        )

        # Act
        result_file_record, result_stream = await use_case.execute(query)

        # Assert
        assert result_file_record == file_record
        assert result_stream is not None

        mock_repository.get_by_id.assert_called_once_with('test-file-id')
        mock_storage_service.download_file.assert_called_once_with(
            bucket_name='test-bucket',
            file_path='test-file-id',
        )

    @pytest.mark.asyncio
    async def test_download_file__file_not_found__raise_file_not_found_error(
        self,
        mock_storage_service,
        mock_repository,
    ):
        """Test download with file not found."""
        # Arrange
        query = DownloadFileQuery(file_id='missing-file-id', user_id=1)

        mock_repository.get_by_id.return_value = None

        use_case = DownloadFileUseCase(
            file_repository=mock_repository,
            storage_service=mock_storage_service,
        )

        # Act & Assert
        with pytest.raises(DomainFileNotFoundError):
            await use_case.execute(query)
