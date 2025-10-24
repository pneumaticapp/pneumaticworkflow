# mypy: disable-error-code="arg-type"
from src.domain.entities import FileRecord
from src.shared_kernel.database.models import FileRecordORM


class FileRecordMapper:
    @staticmethod
    def orm_to_entity(orm: FileRecordORM) -> FileRecord:
        """
        Convert ORM to domain entity
        """
        return FileRecord(
            file_id=orm.file_id,
            filename=orm.filename,
            content_type=orm.content_type,
            size=orm.size,
            user_id=orm.user_id,
            account_id=orm.account_id,
            created_at=orm.created_at,
        )

    @staticmethod
    def entity_to_orm(entity: FileRecord) -> FileRecordORM:
        """
        Convert domain entity to ORM
        """
        return FileRecordORM(
            file_id=entity.file_id,
            filename=entity.filename,
            content_type=entity.content_type,
            size=entity.size,
            user_id=entity.user_id,
            account_id=entity.account_id,
            created_at=entity.created_at,
        )
