"""Abruptly exit after object write, deliberately skipping Python cleanup."""

import asyncio
import os
import sys
from io import BytesIO
from pathlib import Path
from typing import IO

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.dto import UploadFileCommand
from src.application.use_cases.mcp_upload import MCPUploadService
from src.shared_kernel.auth.mcp import FileGrant
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.middleware.auth_middleware import AuthUser


class CrashStorage:
    """Persist test bytes outside the doomed process, then terminate it."""

    def __init__(self, directory: Path):
        self.directory = directory

    def get_storage_path(
        self,
        account_id: int,
        file_id: str,
    ) -> tuple[str, str]:
        return f'test-{account_id}', file_id

    async def upload_file(
        self,
        bucket_name: str,
        file_path: str,
        file_stream: IO[bytes],
        content_type: str | None,
    ):
        payload = file_stream.read()
        (self.directory / file_path).write_bytes(payload)
        os._exit(73)


class CrashUpload(MCPUploadService):
    """Keep this failure test independent of external core availability."""

    async def _revalidate(self, user: AuthUser, operation: str):
        # The crash child must never contact core or external S3.
        assert user.mcp_connection_id == 'conn-1'
        assert operation == 'upload'


async def main():
    schema, directory = sys.argv[1:]
    engine = create_async_engine(
        os.environ['MCP_TEST_DATABASE_URL'],
        execution_options={'schema_translate_map': {None: schema}},
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    user = FileGrant(
        active=True,
        user_id=1,
        account_id=10,
        connection_id='conn-1',
        operation='upload',
        upload_session_id='session-1',
    ).user(credential='mcp-u_upload')
    async with sessions() as session:
        await CrashUpload(
            session=session,
            storage=CrashStorage(directory=Path(directory)),
            settings=BaseAppSettings(_env_file=None),
        ).execute(
            command=UploadFileCommand(
                file_stream=BytesIO(b'crash-surviving-bytes'),
                filename='crash.txt',
                content_type='text/plain',
                size=len(b'crash-surviving-bytes'),
                user_id=1,
                account_id=10,
            ),
            user=user,
        )


if __name__ == '__main__':
    asyncio.run(main())
