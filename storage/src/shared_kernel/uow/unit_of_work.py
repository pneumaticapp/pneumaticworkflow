"""Unit of Work implementation"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Unit of Work for managing transactions"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._transaction: Any | None = None

    async def __aenter__(self) -> 'UnitOfWork':
        """Start transaction"""
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        """End transaction"""
        if self._transaction:
            await self._transaction.__aexit__(*args)
            self._transaction = None

    async def commit(self) -> None:
        """Commit transaction"""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback transaction"""
        await self._session.rollback()
