"""Streaming upload admission does not trust Content-Length."""

import httpx
from fastapi import FastAPI, Request
from pytest_mock import MockerFixture

from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.middleware.mcp_upload_limit import (
    MCPUploadLimitMiddleware,
)


async def test_chunked__upload_stops_before_reading_entire_body__ok(
    mocker: MockerFixture,
):
    # arrange
    settings = BaseAppSettings(MCP_MAX_IMPORT_BYTES=4)
    settings_mock = mocker.patch(
        'src.shared_kernel.middleware.mcp_upload_limit.get_settings',
        return_value=settings,
    )
    mocker.patch(
        'src.shared_kernel.middleware.mcp_upload_limit.MULTIPART_OVERHEAD_BYTES',
        0,
    )
    application = FastAPI()
    application.add_middleware(MCPUploadLimitMiddleware)
    consumed = []

    @application.post('/upload')
    async def upload(request: Request):
        async for chunk in request.stream():
            consumed.append(chunk)
        return {'ok': True}

    yielded = []

    async def chunks():
        for value in (b'123', b'456', b'789'):
            yielded.append(value)
            yield value

    # act
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url='https://example.com',
    ) as client:
        response = await client.post(
            url='/upload',
            headers={'Authorization': 'Bearer mcp-u_upload'},
            content=chunks(),
        )

    # assert
    assert response.status_code == 413
    assert yielded == [b'123', b'456']
    assert consumed == [b'123']
    settings_mock.assert_called_once_with()
