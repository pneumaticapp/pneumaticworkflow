"""Data mappers for converting between ORM and domain entities."""

from src.domain.entities import FileRecord
from src.shared_kernel.database.models import FileRecordORM


class FileRecordMapper:
    """File record mapper between ORM and domain entities."""

    @staticmethod
    def orm_to_entity(orm: FileRecordORM) -> FileRecord:
        """Convert ORM to domain entity."""
        return FileRecord(
            file_id=orm.file_id,  # type: ignore[arg-type]
            filename=orm.filename,  # type: ignore[arg-type]
            content_type=orm.content_type,  # type: ignore[arg-type]
            size=orm.size,  # type: ignore[arg-type]
            user_id=orm.user_id,  # type: ignore[arg-type]
            account_id=orm.account_id,  # type: ignore[arg-type]
            created_at=orm.created_at,  # type: ignore[arg-type]
        )

    @staticmethod
    def entity_to_orm(entity: FileRecord) -> FileRecordORM:
        """Convert domain entity to ORM."""
        return FileRecordORM(
            file_id=entity.file_id,
            filename=entity.filename,
            content_type=entity.content_type,
            size=entity.size,
            user_id=entity.user_id,
            account_id=entity.account_id,
            created_at=entity.created_at,
        )
