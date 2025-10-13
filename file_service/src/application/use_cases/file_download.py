"""File download use case"""

from typing import Any, AsyncIterator, Tuple

from src.application.dto import DownloadFileQuery
from src.domain.entities import FileRecord
from src.infra.repositories import FileRecordRepository
from src.shared_kernel.exceptions import FileNotFoundError


class DownloadFileUseCase:
    """File download use case"""

    def __init__(
        self,
        file_repository: FileRecordRepository,
        storage_service: Any,  # StorageService
    ) -> None:
        """Initialize download file use case

        Args:
        ----
            file_repository: File repository
            storage_service: File storage service
        """
        self._file_repository = file_repository
        self._storage_service = storage_service

    async def execute(
        self,
        query: DownloadFileQuery,
    ) -> Tuple[FileRecord, AsyncIterator[bytes]]:
        """
        Execute file download with file info

        Args:
        ----
            query: File download query

        Returns:
        -------
            Tuple[FileRecord, AsyncIterator[bytes]]: File info and byte stream

        Raises:
        ------
            FileNotFoundError: If file not found
        """
        # Get file information from database
        file_record = await self._file_repository.get_by_id(query.file_id)
        if not file_record:
            raise FileNotFoundError(query.file_id)

        # Get S3 download paths from StorageService
        bucket_name, file_path = self._storage_service.get_storage_path(
            file_record.account_id,
            file_record.file_id,
        )

        # Stream file from S3
        stream = self._storage_service.download_file(
            bucket_name=bucket_name,
            file_path=file_path,
        )

        return file_record, stream
