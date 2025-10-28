"""File upload use case."""

from datetime import UTC, datetime
from uuid import uuid4

from src.application.dto import UploadFileCommand, UploadFileUseCaseResponse
from src.domain.entities import FileRecord
from src.infra.repositories import FileRecordRepository
from src.infra.repositories.storage_service import StorageService
from src.shared_kernel.uow import UnitOfWork


class UploadFileUseCase:
    """File upload use case."""

    def __init__(
        self,
        file_repository: FileRecordRepository,
        storage_service: StorageService,
        unit_of_work: UnitOfWork,
        fastapi_base_url: str,
    ) -> None:
        """Initialize upload file use case.

        Args:
            file_repository: File repository.
            storage_service: File storage service.
            unit_of_work: Unit of Work for transactions.
            fastapi_base_url: FastAPI application base URL.

        """
        self._file_repository = file_repository
        self._storage_service = storage_service
        self._unit_of_work = unit_of_work
        self._fastapi_base_url = fastapi_base_url

    async def execute(
        self,
        command: UploadFileCommand,
    ) -> UploadFileUseCaseResponse:
        """Execute file upload.

        Args:
            command: File upload command.

        Returns:
            FileUploadResponse: File upload result.

        """
        # Create domain file entity
        file_record = FileRecord(
            file_id=str(uuid4()),
            filename=command.filename,
            content_type=command.content_type,
            size=command.size,
            user_id=command.user_id,
            account_id=command.account_id,
            created_at=datetime.now(UTC),
        )

        # Get S3 storage paths from StorageService
        bucket_name, file_path = self._storage_service.get_storage_path(
            file_record.account_id,
            file_record.file_id,
        )

        # Upload file to S3
        await self._storage_service.upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            file_content=command.file_content,
            content_type=command.content_type,
        )

        # Save record to database
        async with self._unit_of_work:
            await self._file_repository.create(file_record)
            await self._unit_of_work.commit()

        # Generate public download URL
        public_url = f'{self._fastapi_base_url}/{file_record.file_id}'

        return UploadFileUseCaseResponse(
            file_id=file_record.file_id,
            public_url=public_url,
        )
