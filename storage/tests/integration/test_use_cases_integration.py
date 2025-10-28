from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from src.application.dto.file_dtos import DownloadFileQuery, UploadFileCommand
from src.application.use_cases.file_download import DownloadFileUseCase
from src.application.use_cases.file_upload import UploadFileUseCase
from src.domain.entities.file_record import FileRecord
from src.infra.repositories.file_record_repository import FileRecordRepository
from src.infra.repositories.storage_service import StorageService
from src.shared_kernel.exceptions import DomainFileNotFoundError
from src.shared_kernel.uow import UnitOfWork


class TestUploadFileUseCaseIntegration:
    """Test UploadFileUseCase integration"""

    @pytest.mark.asyncio
    async def test_upload_file__full_integration__ok(
        self,
        async_session,
        mock_aioboto3_session,
    ):
        """Test full upload file integration"""
        # Arrange
        repository = FileRecordRepository(async_session)
        storage_service = StorageService()
        unit_of_work = UnitOfWork(async_session)
        use_case = UploadFileUseCase(
            file_repository=repository,
            storage_service=storage_service,
            unit_of_work=unit_of_work,
            fastapi_base_url='http://localhost:8000',
        )

        command = UploadFileCommand(
            file_content=b'test file content',
            filename='test_file.txt',
            content_type='text/plain',
            size=18,
            user_id=1,
            account_id=1,
        )

        mock_s3_client = AsyncMock()
        (
            mock_aioboto3_session.return_value.client.return_value.__aenter__
        ).return_value = mock_s3_client

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is not None
        assert result.file_id is not None
        assert result.public_url is not None
        assert result.public_url.startswith('http://localhost:8000/')

        # Check that record is created in DB
        await async_session.commit()
        file_record = await repository.get_by_id(result.file_id)
        assert file_record is not None
        assert file_record.filename == 'test_file.txt'
        assert file_record.content_type == 'text/plain'
        assert file_record.size == 18
        assert file_record.user_id == 1
        assert file_record.account_id == 1

    @pytest.mark.parametrize(
        ('content_type', 'filename', 'content'),
        [
            ('text/plain', 'document.txt', b'This is a text file with some'),
            ('image/png', 'image.png', b'\x89PNG\r\n\x1a\n' + b'x' * 1000),
            ('application/pdf', 'document.pdf', b'%PDF-1.4\n' + b'x' * 2000),
            (
                'application/json',
                'data.json',
                b'{"key": "value", "number": 42}',
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_upload_file__different_content_types__upload_successfully(
        self,
        content_type,
        filename,
        content,
        async_session,
        mock_aioboto3_session,
    ):
        """Test upload file with different content types"""
        # Arrange
        repository = FileRecordRepository(async_session)
        storage_service = StorageService()
        unit_of_work = UnitOfWork(async_session)
        use_case = UploadFileUseCase(
            file_repository=repository,
            storage_service=storage_service,
            unit_of_work=unit_of_work,
            fastapi_base_url='http://localhost:8000',
        )

        command = UploadFileCommand(
            file_content=content,
            filename=filename,
            content_type=content_type,
            size=len(content),
            user_id=1,
            account_id=1,
        )

        mock_s3_client = AsyncMock()
        (
            mock_aioboto3_session.return_value.client.return_value.__aenter__
        ).return_value = mock_s3_client

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result is not None
        assert result.file_id is not None
        assert result.public_url is not None

        # Check that record is created in DB
        await async_session.commit()
        file_record = await repository.get_by_id(result.file_id)
        assert file_record is not None
        assert file_record.filename == filename
        assert file_record.content_type == content_type
        assert file_record.size == len(content)


class TestDownloadFileUseCaseIntegration:
    """Test DownloadFileUseCase integration"""

    @pytest.mark.asyncio
    async def test_download_file__full_integration__ok(
        self,
        async_session,
        mock_aioboto3_session,
    ):
        """Test full download file integration"""
        # Arrange
        repository = FileRecordRepository(async_session)
        storage_service = StorageService()
        use_case = DownloadFileUseCase(
            file_repository=repository,
            storage_service=storage_service,
        )

        # Create record in DB
        file_record = FileRecord(
            file_id='test-file-id',
            filename='test_file.txt',
            content_type='text/plain',
            size=18,
            user_id=1,
            account_id=1,
            created_at=datetime.now(),
        )
        await repository.create(file_record)
        await async_session.commit()

        query = DownloadFileQuery(file_id='test-file-id', user_id=1)

        mock_s3_client = AsyncMock()

        # Create mock for async generator
        async def mock_iter_chunks(chunk_size=None):
            yield b'test file content'

        mock_body = AsyncMock()
        mock_body.iter_chunks = mock_iter_chunks

        mock_s3_client.get_object.return_value = {'Body': mock_body}
        (
            mock_aioboto3_session.return_value.client.return_value.__aenter__
        ).return_value = mock_s3_client

        # Act
        result_file_record, result_stream = await use_case.execute(query)

        # Assert
        assert result_file_record is not None
        assert result_file_record.file_id == 'test-file-id'
        assert result_file_record.filename == 'test_file.txt'
        assert result_stream is not None

        # Check stream content
        content = b''
        async for chunk in result_stream:
            content += chunk

        assert content == b'test file content'

    @pytest.mark.asyncio
    async def test_download_file__file_not_found__raise_file_not_found_error(
        self,
        async_session,
        mock_aioboto3_session,
    ):
        """Test download nonexistent file"""
        # Arrange
        repository = FileRecordRepository(async_session)
        storage_service = StorageService()
        use_case = DownloadFileUseCase(
            file_repository=repository,
            storage_service=storage_service,
        )

        query = DownloadFileQuery(file_id='nonexistent-file-id', user_id=1)

        # Act & Assert
        with pytest.raises(DomainFileNotFoundError):
            await use_case.execute(query)
