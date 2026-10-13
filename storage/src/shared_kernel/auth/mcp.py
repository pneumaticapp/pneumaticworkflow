"""Live core authorization for restricted file delegation credentials."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

import asyncio
import time
import unicodedata
from typing import Any, NotRequired, TypedDict, Unpack
from urllib.parse import quote

import httpx
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.shared_kernel.auth.user_types import UserType
from src.shared_kernel.config import get_settings
from src.shared_kernel.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
)
from src.shared_kernel.exceptions.mcp_exceptions import (
    MCPCoreUnavailableError,
    MCPUploadConflictError,
)
from src.shared_kernel.middleware.auth_middleware import AuthUser


class FileValidationRequest(TypedDict):
    """Named, optional provenance supplied to the private core validator."""

    operation: str
    credential: NotRequired[str | None]
    connection_id: NotRequired[str]
    upload_session_id: NotRequired[str | None]
    authorization_id: NotRequired[str]
    file_id: NotRequired[str]


class FileGrant(BaseModel):
    """The live identity returned by the trusted core file validator."""

    model_config = ConfigDict(strict=True)
    active: bool
    user_id: int = Field(gt=0)
    account_id: int = Field(gt=0)
    connection_id: str = Field(min_length=1, max_length=128)
    operation: str
    upload_session_id: str | None = None
    authorization_id: str | None = None
    expires_at: int | None = Field(default=None, gt=0)

    def user(self, credential: str | None = None) -> AuthUser:
        """Build an audit-compatible user carrying delegation provenance."""
        return AuthUser(
            auth_type=UserType.AUTHENTICATED,
            user_id=self.user_id,
            account_id=self.account_id,
            token=credential,
            mcp_connection_id=self.connection_id,
            mcp_upload_session_id=self.upload_session_id,
            mcp_authorization_id=self.authorization_id,
            mcp_authorization_expires_at=self.expires_at,
        )


class MCPCoreClient:
    """Call the configured private core with a distinct service secret."""

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Deny disabled MCP, outages, denial and malformed replies."""
        settings = get_settings()
        secret = settings.MCP_FILE_SERVICE_SECRET.get_secret_value()
        if not settings.MCP_ENABLED or not secret:
            raise AuthenticationError(details='MCP file access is disabled')
        try:
            async with (
                asyncio.timeout(10),
                httpx.AsyncClient(
                    trust_env=False,
                    timeout=10,
                    follow_redirects=False,
                ) as client,
            ):
                response = await client.post(
                    f'{settings.MCP_BACKEND_URL.rstrip("/")}{path}',
                    headers={'Authorization': f'Bearer {secret}'},
                    json=body,
                )
            result = None
            if response.status_code == 200:  # noqa: PLR2004
                result = response.json()
        except (httpx.HTTPError, TimeoutError, ValueError, TypeError):
            raise MCPCoreUnavailableError from None
        if response.status_code == 401:  # noqa: PLR2004
            # This Authorization authenticates the storage service itself.
            # A rejected private secret is an outage, not a user login failure.
            raise MCPCoreUnavailableError
        if response.status_code == 403:  # noqa: PLR2004
            raise PermissionDeniedError(details='MCP file access denied')
        if response.status_code == 409:  # noqa: PLR2004
            raise MCPUploadConflictError
        if response.status_code != 200:  # noqa: PLR2004
            raise MCPCoreUnavailableError
        if not isinstance(result, dict):
            raise MCPCoreUnavailableError
        return result

    async def validate(
        self, **body: Unpack[FileValidationRequest]
    ) -> FileGrant:
        """Recheck connection, user, account, scope and object in core."""
        result = await self.post(
            path='/internal/mcp/validate-files',
            body=dict(body),
        )
        if result.get('active') is False:
            raise AuthenticationError(details='MCP file access denied')
        try:
            grant = FileGrant.model_validate(result)
        except ValidationError:
            raise MCPCoreUnavailableError from None
        if not grant.active or grant.operation != body['operation']:
            raise PermissionDeniedError(details='MCP file operation denied')
        if (
            grant.operation in ('metadata', 'download')
            and grant.expires_at is None
        ):
            raise MCPCoreUnavailableError
        if grant.expires_at is not None and grant.expires_at <= time.time():
            raise AuthenticationError(details='Expired MCP file authorization')
        for field in (
            'connection_id',
            'upload_session_id',
            'authorization_id',
        ):
            if (
                body.get(field) is not None
                and getattr(grant, field) != body[field]
            ):
                raise AuthenticationError(
                    details='MCP grant identity mismatch'
                )
        return grant


def is_mcp_request(request: Request) -> bool:
    """Recognize MCP even when an ordinary browser credential is also set."""
    authorization = request.headers.get('authorization', '')
    cookies = getattr(request, 'cookies', {})
    return (
        'x-mcp-delegation' in request.headers
        or 'x-mcp-upload-session' in request.headers
        or any(
            part.startswith('mcp-') for part in authorization.lower().split()
        )
        or any(
            isinstance(value := cookies.get(name), str)
            and value.lower().startswith('mcp-')
            for name in ('token', 'file_service_auth')
        )
        or request.url.path.removeprefix(
            getattr(request, 'scope', {}).get('root_path', ''),
        ).startswith('/mcp/')
    )


def _require_flat_read_path(  # noqa: ANN202
    request: Request,
    path: str,
    file_id: str,
):
    if (
        not 1 <= len(file_id) <= 512  # noqa: PLR2004
        or not file_id.strip()
        or file_id in ('.', '..')
        or any(char in file_id for char in '/\\?#%')
        or any(
            unicodedata.category(char).startswith('C')
            or unicodedata.category(char) in ('Zl', 'Zp')
            for char in file_id
        )
    ):
        raise AuthenticationError(details='Invalid MCP file identifier')
    encoded = quote(file_id, safe='')
    canonical = (
        '/mcp/files/' + encoded
        if path.startswith('/mcp/files/')
        else '/' + encoded
    )
    if request.method == 'POST':
        canonical += '/download-ticket'
    root_path = request.scope.get('root_path', '')
    if root_path and request.scope['path'].startswith(root_path + '/'):
        canonical = root_path + canonical
    if request.scope.get('raw_path') != canonical.encode('ascii'):
        raise AuthenticationError(details='Noncanonical MCP file path')


def _request_credential(request: Request) -> str:
    authorization = request.headers.get('authorization', '')
    credential = request.headers.get('x-mcp-delegation')
    if credential is None and authorization.lower().startswith('bearer '):
        credential = authorization[7:]
    if not credential or len(credential) > 2048:  # noqa: PLR2004
        raise AuthenticationError(details='Missing MCP credential')
    return credential


async def authenticate_mcp_request(request: Request) -> AuthUser:  # noqa: PLR0912
    """Bind credentials to the route without ordinary auth fallback."""
    credential = _request_credential(request=request)
    # ASGI already decoded this path once. URL.path can interpret a decoded
    # question/hash as query/fragment and authorize a different file ID.
    path = request.scope['path'].removeprefix(
        getattr(request, 'scope', {}).get('root_path', ''),
    )
    body: FileValidationRequest = {'credential': credential, 'operation': ''}
    if path == '/upload' and request.method == 'POST':
        body['operation'] = 'upload'
        session_id = request.headers.get('x-mcp-upload-session')
        if session_id is not None:
            body['upload_session_id'] = session_id
    elif path.startswith('/mcp/files/'):
        pieces = path.split('/')
        body['file_id'] = pieces[3]
        if len(pieces) == 4 and request.method == 'GET':  # noqa: PLR2004
            body['operation'] = 'metadata'
        elif (
            len(pieces) == 5  # noqa: PLR2004
            and pieces[4] == 'download-ticket'
            and request.method == 'POST'
        ):
            body['operation'] = 'download'
        else:
            raise AuthenticationError(details='Invalid MCP file operation')
    elif path.count('/') == 1 and request.method == 'GET':
        body['operation'] = 'download'
        body['file_id'] = path[1:]
    else:
        raise AuthenticationError(details='Invalid MCP file operation')
    file_id = body.get('file_id')
    if file_id is not None:
        _require_flat_read_path(request=request, path=path, file_id=file_id)
    grant = await MCPCoreClient().validate(**body)
    if body['operation'] == 'upload' and not grant.upload_session_id:
        raise AuthenticationError(details='Missing core upload session')
    return grant.user(credential=credential)
