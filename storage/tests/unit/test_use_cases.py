"""Tests for use cases (upload/download)."""

import io
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, Mock

import pytest

from src.application.dto.file_dtos import (
    DownloadFileQuery,
    UploadFileCommand,
    UploadFileUseCaseResponse,
)
from src.application.use_cases.file_download import (
    DownloadFileUseCase,
)
from src.application.use_cases.file_upload import UploadFileUseCase
from src.domain.entities.file_record import FileRecord
from src.shared_kernel.exceptions import (
    DomainFileNotFoundError,
    StorageError,
)

# --- UploadFileUseCase ---


@pytest.mark.asyncio
async def test_upload__valid_command__return_response(
    mock_storage_service,
    mock_repository,
):
    # arrange
    command = UploadFileCommand(
        file_stream=io.BytesIO(b'test content'),
        filename='test.txt',
        content_type='text/plain',
        size=12,
        user_id=1,
        account_id=1,
    )
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='test.txt',
        content_type='text/plain',
        size=12,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    mock_uow = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None
    mock_repository.create.return_value = file_record
    mock_storage_service.get_storage_path.return_value = (
        'test-bucket',
        '12345678-1234-5678-1234-567812345678',
    )
    mock_storage_service.upload_file.return_value = None
    use_case = UploadFileUseCase(
        file_repository=mock_repository,
        storage_service=mock_storage_service,
        unit_of_work=mock_uow,
        fastapi_base_url='http://localhost:8000',
    )

    # act
    result = await use_case.execute(command=command)

    # assert
    assert isinstance(result, UploadFileUseCaseResponse)
    assert result.file_id is not None
    assert result.public_url.startswith(
        'http://localhost:8000/',
    )
    assert result.file_id in result.public_url
    mock_repository.create.assert_called_once_with(ANY)
    mock_storage_service.upload_file.assert_called_once_with(
        bucket_name='test-bucket',
        file_path='12345678-1234-5678-1234-567812345678',
        file_stream=ANY,
        content_type='text/plain',
    )


@pytest.mark.asyncio
async def test_upload__storage_error__raise(
    mock_storage_service,
    mock_repository,
):
    # arrange
    command = UploadFileCommand(
        file_stream=io.BytesIO(b'test content'),
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
        '12345678-1234-5678-1234-567812345678',
    )
    mock_storage_service.upload_file.side_effect = StorageError.upload_failed(
        'Upload failed'
    )
    use_case = UploadFileUseCase(
        file_repository=mock_repository,
        storage_service=mock_storage_service,
        unit_of_work=mock_uow,
        fastapi_base_url='http://localhost:8000',
    )

    # act
    with pytest.raises(StorageError):
        await use_case.execute(command=command)


# --- DownloadFileUseCase ---


@pytest.mark.asyncio
async def test_get_metadata__valid__return_record(
    mock_storage_service,
    mock_repository,
):
    # arrange
    query = DownloadFileQuery(
        file_id='12345678-1234-5678-1234-567812345678',
        user_id=1,
    )
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='test.txt',
        content_type='text/plain',
        size=12,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    mock_repository.get_by_id.return_value = file_record
    use_case = DownloadFileUseCase(
        file_repository=mock_repository,
        storage_service=mock_storage_service,
    )

    # act
    result = await use_case.get_metadata(query=query)

    # assert
    assert result == file_record
    mock_repository.get_by_id.assert_called_once_with(
        '12345678-1234-5678-1234-567812345678',
    )
    mock_storage_service.get_storage_path.assert_not_called()
    mock_storage_service.download_file.assert_not_called()


@pytest.mark.asyncio
async def test_get_metadata__not_found__raise(
    mock_storage_service,
    mock_repository,
):
    # arrange
    query = DownloadFileQuery(
        file_id='missing-file-id',
        user_id=1,
    )
    mock_repository.get_by_id.return_value = None
    use_case = DownloadFileUseCase(
        file_repository=mock_repository,
        storage_service=mock_storage_service,
    )

    # act
    with pytest.raises(DomainFileNotFoundError):
        await use_case.get_metadata(query=query)


@pytest.mark.asyncio
async def test_get_stream__valid__return_stream(
    mock_storage_service,
    mock_repository,
):
    # arrange
    file_record = FileRecord(
        file_id='12345678-1234-5678-1234-567812345678',
        filename='test.txt',
        content_type='text/plain',
        size=12,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    mock_storage_service.get_storage_path.return_value = (
        'test-bucket',
        '12345678-1234-5678-1234-567812345678',
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

    # act
    result_stream = await use_case.get_stream(
        file_record=file_record,
    )

    # assert
    assert result_stream is not None
    mock_storage_service.download_file.assert_called_once_with(
        bucket_name='test-bucket',
        file_path='12345678-1234-5678-1234-567812345678',
        range_header=None,
    )
