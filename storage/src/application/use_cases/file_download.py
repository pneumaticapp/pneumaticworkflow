"""File download use case."""

from collections.abc import AsyncIterator

from src.application.dto import DownloadFileQuery
from src.domain.entities import FileRecord
from src.infra.adapters.storage_service import StorageService
from src.infra.repositories import FileRecordRepository
from src.shared_kernel.exceptions import DomainFileNotFoundError


class DownloadFileUseCase:
    """File download use case."""

    def __init__(
        self,
        file_repository: FileRecordRepository,
        storage_service: StorageService,
    ) -> None:
        """Initialize download file use case.

        Args:
            file_repository: File repository.
            storage_service: File storage service.

        """
        self._file_repository = file_repository
        self._storage_service = storage_service

    async def get_metadata(self, query: DownloadFileQuery) -> FileRecord:
        """Get file metadata without loading the stream (fail fast).

        Args:
            query: File download query.

        Returns:
            FileRecord: File metadata.

        Raises:
            DomainFileNotFoundError: If file not found.

        """
        file_record = await self._file_repository.get_by_id(query.file_id)
        if not file_record:
            raise DomainFileNotFoundError(query.file_id)
        return file_record

    async def get_stream(
        self,
        file_record: FileRecord,
        range_header: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Get file stream after permissions are verified.

        Args:
            file_record: File metadata.
            range_header: Optional HTTP Range header.

        Returns:
            AsyncIterator[bytes]: File byte stream.

        """
        # Get S3 download paths from StorageService
        bucket_name, file_path = self._storage_service.get_storage_path(
            file_record.account_id,
            file_record.file_id,
        )

        # Stream file from S3
        return self._storage_service.download_file(
            bucket_name=bucket_name,
            file_path=file_path,
            range_header=range_header,
        )
