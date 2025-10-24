from typing import Optional

from sqlalchemy.exc import (
    DatabaseError as SQLAlchemyDatabaseError,
)
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.entities import FileRecord
from src.infra.mappers import FileRecordMapper
from src.shared_kernel.database.models import FileRecordORM
from src.shared_kernel.exceptions import (
    MSG_DB_009,
    MSG_DB_010,
    DatabaseConnectionError,
    DatabaseConstraintError,
    DatabaseOperationError,
)


class FileRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = FileRecordMapper()

    async def create(self, file_record: FileRecord) -> None:
        """Create file record"""
        try:
            orm_record = self.mapper.entity_to_orm(file_record)
            self.session.add(orm_record)
        except IntegrityError as e:
            raise DatabaseConstraintError(
                constraint='file_record_unique_constraint',
                details=MSG_DB_010.format(details=str(e)),
            ) from e
        except OperationalError as e:
            raise DatabaseConnectionError(
                details=MSG_DB_009.format(operation='create', details=str(e))
            ) from e
        except SQLAlchemyDatabaseError as e:
            raise DatabaseOperationError(
                operation='create_file_record', details=str(e)
            ) from e

    async def get_by_id(self, file_id: str) -> Optional[FileRecord]:
        """Get file record by ID"""
        try:
            stmt = select(FileRecordORM).where(
                FileRecordORM.file_id == file_id
            )
            result = await self.session.execute(stmt)
            orm_record = result.scalar_one_or_none()

            if orm_record is None:
                return None

            return self.mapper.orm_to_entity(orm_record)
        except OperationalError as e:
            raise DatabaseConnectionError(
                details=MSG_DB_009.format(
                    operation='get_by_id', details=str(e)
                )
            ) from e
        except SQLAlchemyDatabaseError as e:
            raise DatabaseOperationError(
                operation='get_file_record_by_id', details=str(e)
            ) from e
