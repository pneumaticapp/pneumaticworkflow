"""Actual storage HTTP server for the isolated core/storage contract smoke.

Run with storage dependencies, PYTHONPATH=/repo/storage and explicit test env:
POSTGRES_DB=mcp_contract_files, POSTGRES_HOST/PORT/USER/PASSWORD,
DJANGO_SECRET_KEY and MCP_FILE_SERVICE_SECRET (same secret as the core smoke).
python -m tests.live_mcp_server --port 18083

Only the S3 dependency is replaced. PostgreSQL, Alembic and auth middleware,
delegation validation, upload callbacks, tickets and permission checks
remain real.
No dotenv files are loaded. The server binds loopback and refuses any
database name except mcp_contract_files. GET /__test_provider__/health reports
readiness; GET/PUT /__test_provider__/objects/{bucket}/{file_id} and GET
/__test_provider__/stats require Bearer MCP_FILE_SERVICE_SECRET.
"""

import argparse
import asyncio
import os
import re
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import IO

import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from src.shared_kernel.config import get_settings
from src.shared_kernel.security import sanitize_content_type


class MemoryStorage:
    """An in-process replacement for S3 bytes, with idempotent deletion."""

    def __init__(self, bucket_prefix: str):
        self.bucket_prefix = bucket_prefix
        self.objects: dict[tuple[str, str], tuple[bytes, str | None]] = {}

    def get_storage_path(
        self, account_id: int, file_id: str
    ) -> tuple[str, str]:
        return f'{self.bucket_prefix}-{account_id}', file_id

    async def upload_file(
        self,
        bucket_name: str,
        file_path: str,
        file_stream: IO[bytes],
        content_type: str | None,
    ):
        payload = await asyncio.to_thread(file_stream.read)
        self.objects[bucket_name, file_path] = payload, content_type

    async def download_file(
        self,
        bucket_name: str,
        file_path: str,
        range_header: str | None = None,
    ) -> AsyncIterator[bytes]:
        item = self.objects.get((bucket_name, file_path))
        if item is None:
            raise HTTPException(404, 'Test provider object not found')
        payload = item[0]
        if range_header:
            match = re.fullmatch(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match[1])
                end = int(match[2]) + 1 if match[2] else len(payload)
                payload = payload[start:end]

        async def stream() -> AsyncIterator[bytes]:
            yield payload

        return stream()

    async def delete_file(self, bucket_name: str, file_path: str):
        self.objects.pop((bucket_name, file_path), None)


def prepare_database():
    """Apply the entire real migration chain to the explicitly isolated DB."""
    if os.environ.get('POSTGRES_DB') != 'mcp_contract_files':
        msg = 'The live helper requires POSTGRES_DB=mcp_contract_files'
        raise RuntimeError(msg)
    config_path = (
        Path(__file__).resolve().parents[1]
        / 'src/shared_kernel/database/alembic.ini'
    )
    config = Config(str(config_path))
    config.set_main_option(
        'script_location', str(config_path.parent / 'migrations')
    )
    command.upgrade(config, 'head')


def create_app() -> FastAPI:  # noqa: C901
    """Mount the production app with just one provider dependency override."""
    # App/DI imports initialize settings; wait for the dotenv-free test setup.
    from src.main import app as storage_app  # noqa: PLC0415
    from src.shared_kernel.di.container import (  # noqa: PLC0415
        get_storage_service,
    )

    settings = get_settings()
    provider = MemoryStorage(settings.BUCKET_PREFIX)

    async def memory_provider() -> AsyncIterator[MemoryStorage]:
        yield provider

    storage_app.dependency_overrides[get_storage_service] = memory_provider

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        async with storage_app.router.lifespan_context(storage_app):
            yield

    application = FastAPI(lifespan=lifespan, docs_url=None, openapi_url=None)

    def require_provider_secret(request: Request):
        expected = settings.MCP_FILE_SERVICE_SECRET.get_secret_value()
        received = request.headers.get('authorization', '')
        if not secrets.compare_digest(
            received.encode(), f'Bearer {expected}'.encode()
        ):
            raise HTTPException(
                401, 'Test provider service authentication required'
            )

    @application.get('/__test_provider__/health')
    async def health() -> dict[str, bool]:
        return {'ready': True}

    @application.get('/__test_provider__/stats')
    async def stats(request: Request) -> dict[str, int]:
        require_provider_secret(request)
        return {'objects': len(provider.objects)}

    @application.put('/__test_provider__/objects/{bucket}/{file_id}')
    async def put_object(
        bucket: str, file_id: str, request: Request
    ) -> dict[str, int]:
        require_provider_secret(request)
        payload = await request.body()
        if len(payload) > settings.MCP_MAX_IMPORT_BYTES:
            raise HTTPException(413, 'Test provider object is too large')
        provider.objects[bucket, file_id] = (
            payload,
            request.headers.get('content-type'),
        )
        return {'size': len(payload)}

    @application.get('/__test_provider__/objects/{bucket}/{file_id}')
    async def get_object(
        bucket: str, file_id: str, request: Request
    ) -> Response:
        require_provider_secret(request)
        item = provider.objects.get((bucket, file_id))
        if item is None:
            raise HTTPException(404, 'Test provider object not found')
        return Response(
            item[0],
            media_type=sanitize_content_type(item[1]),
            headers={'Cache-Control': 'no-store'},
        )

    application.mount('/', storage_app)
    return application


def main():
    """Start on test-container loopback, without reading checkout envs."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18083)
    parser.add_argument('--migrate-only', action='store_true')
    args = parser.parse_args()
    os.environ['CONFIG'] = 'Testing'
    os.environ['MCP_ENABLED'] = 'yes'
    os.environ.setdefault('MCP_BACKEND_URL', 'http://127.0.0.1:18081')
    os.environ.setdefault('FASTAPI_BASE_URL', 'https://pneumatic.test/files')
    os.environ['SENTRY_DSN'] = ''
    os.environ['LOGS_BACKEND'] = ''
    os.environ['LOGS_REDIS_URL'] = ''
    # Pydantic dotenv paths are relative to CWD. Keep this helper independent
    # of any actual checkout secrets while using the normal settings factory.
    original_cwd = Path.cwd()
    with TemporaryDirectory(prefix='storage-mcp-http-') as isolated_cwd:
        try:
            os.chdir(isolated_cwd)
            prepare_database()
            if not args.migrate_only:
                uvicorn.run(
                    create_app(),
                    host='127.0.0.1',
                    port=args.port,
                    log_level='info',
                    access_log=False,
                )
        finally:
            os.chdir(original_cwd)


if __name__ == '__main__':
    main()
