"""Issue and validate revocable file download tickets."""

import hashlib
import math
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared_kernel.auth.dependencies import AuthenticatedUser
from src.shared_kernel.auth.mcp import FileGrant, MCPCoreClient
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.database.models import MCPDownloadTicketORM
from src.shared_kernel.exceptions import AuthenticationError
from src.shared_kernel.exceptions.mcp_exceptions import MCPCoreUnavailableError

TICKET_SECONDS = 300


class MCPDownloadService:
    """Persist ticket hashes and recheck source authorization on every use."""

    def __init__(
        self, session: AsyncSession, settings: BaseAppSettings
    ) -> None:
        """Bind ticket storage and the public file service URL."""
        self.session = session
        self.settings = settings

    async def issue(
        self, file_id: str, user: AuthenticatedUser
    ) -> dict[str, Any]:
        """Issue a ticket after the caller has verified attachment metadata."""
        now = datetime.now(UTC)
        authorized_expiry = user.mcp_authorization_expires_at
        if not user.mcp_authorization_id or authorized_expiry is None:
            raise MCPCoreUnavailableError
        if authorized_expiry <= now.timestamp():
            raise AuthenticationError(details='Expired MCP file authorization')
        expires = now + timedelta(seconds=TICKET_SECONDS)
        if authorized_expiry < expires.timestamp():
            expires = datetime.fromtimestamp(authorized_expiry, UTC)
        token = secrets.token_urlsafe(32)
        await self.session.execute(
            delete(MCPDownloadTicketORM).where(
                MCPDownloadTicketORM.expires_at <= now,
            )
        )
        self.session.add(
            MCPDownloadTicketORM(
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                connection_id=user.mcp_connection_id,
                authorization_id=user.mcp_authorization_id,
                user_id=user.user_id,
                account_id=user.account_id,
                file_id=file_id,
                expires_at=expires,
            )
        )
        await self.session.commit()
        return {
            'download_url': (
                f'{self.settings.FASTAPI_BASE_URL}/mcp/download/{token}'
            ),
            'expires_at': expires.isoformat(),
            'expires_in': min(
                TICKET_SECONDS, math.ceil((expires - now).total_seconds())
            ),
        }

    async def authorize(self, ticket: str) -> tuple[str, FileGrant]:
        """Validate ticket expiry, revocation and the current file identity."""
        mapping = await self.session.get(
            MCPDownloadTicketORM,
            hashlib.sha256(ticket.encode()).hexdigest(),
        )
        if mapping is None:
            raise AuthenticationError(details='Invalid download ticket')
        expires = mapping.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires <= datetime.now(UTC):
            raise AuthenticationError(details='Expired download ticket')
        grant = await MCPCoreClient().validate(
            operation='download',
            connection_id=mapping.connection_id,
            authorization_id=mapping.authorization_id,
            file_id=mapping.file_id,
        )
        if (grant.account_id, grant.user_id) != (
            mapping.account_id,
            mapping.user_id,
        ):
            raise AuthenticationError(
                details='Download ticket identity mismatch'
            )
        return mapping.file_id, grant
