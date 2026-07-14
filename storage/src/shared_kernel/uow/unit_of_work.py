"""Unit of Work implementation."""

import typing

from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction


class UnitOfWork:
    """Unit of Work for managing transactions."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize Unit of Work.

        Args:
            session: Database session to manage.

        """
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> typing.Self:
        """Start transaction."""
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        return self

    async def __aexit__(self, *args: object) -> None:
        """End transaction."""
        if self._transaction:
            await self._transaction.__aexit__(*args)
            self._transaction = None

    async def commit(self) -> None:
        """Commit transaction."""
        if self._transaction:
            await self._transaction.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        if self._transaction:
            await self._transaction.rollback()
