"""Bound MCP multipart uploads while the ASGI request body is consumed."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.infra.url_importer import MAX_IMPORT_BYTES
from src.shared_kernel.config import get_settings

MULTIPART_OVERHEAD_BYTES = 64 * 1024


class MCPUploadLimitMiddleware:
    """Cap streaming bytes before multipart parsing spools the whole file."""

    def __init__(self, app: ASGIApp):  # noqa: ANN204
        """Bind the ASGI application."""
        self.app = app

    async def __call__(  # noqa: ANN204
        self, scope: Scope, receive: Receive, send: Send
    ):
        """Count incoming chunks independently of claimed Content-Length."""
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        path = scope.get('path', '').removeprefix(scope.get('root_path', ''))
        if (
            scope.get('method') != 'POST'
            or path != '/upload'
            or not (
                headers.get('authorization', '')
                .lower()
                .startswith('bearer mcp-')
                or 'x-mcp-delegation' in headers
                or 'x-mcp-upload-session' in headers
            )
        ):
            await self.app(scope, receive, send)
            return
        settings = get_settings()
        limit = (
            min(
                settings.MAX_FILE_SIZE,
                settings.MCP_MAX_IMPORT_BYTES,
                MAX_IMPORT_BYTES,
            )
            + MULTIPART_OVERHEAD_BYTES
        )
        try:
            content_length = int(headers.get('content-length', '0'))
        except ValueError:
            content_length = 0
        if content_length > limit:
            await JSONResponse(
                status_code=413,
                content={'detail': 'MCP upload size limit exceeded'},
            )(scope, receive, send)
            return
        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message['type'] == 'http.request':
                consumed += len(message.get('body', b''))
                if consumed > limit:
                    raise HTTPException(413, 'MCP upload size limit exceeded')
            return message

        await self.app(scope, limited_receive, send)
