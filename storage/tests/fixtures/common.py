import ast
import asyncio
import hashlib
from collections.abc import AsyncIterator, Callable, Generator
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, Mock, call
from uuid import NAMESPACE_URL, uuid5

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from src.application.dto import UploadFileCommand
from src.application.use_cases.mcp_upload import MCPUploadService
from src.domain.entities import FileRecord
from src.main import app
from src.presentation.api.files import (
    router as files_router,
)
from src.presentation.api.mcp_files import router as mcp_router
from src.shared_kernel.auth.mcp import FileGrant
from src.shared_kernel.config import BaseAppSettings
from src.shared_kernel.database.base import Base
from src.shared_kernel.database.models import (
    FileRecordORM,
    MCPDownloadTicketORM,
    MCPUploadAttemptORM,
    MCPUploadORM,
)
from src.shared_kernel.di.container import (
    get_db_session,
    get_download_use_case,
    get_http_client,
    get_settings_dep,
    get_storage_service,
)
from src.shared_kernel.events.request_events import get_request_events
from src.shared_kernel.exceptions import (
    register_exception_handlers,
)
from src.shared_kernel.middleware.auth_middleware import (
    AuthenticationMiddleware,
    AuthUser,
)
from src.shared_kernel.middleware.security_headers import (
    SecurityHeadersMiddleware,
)


@pytest.fixture(scope='session')
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> BaseAppSettings:
    """Test settings."""
    return BaseAppSettings(
        DEBUG=True,
        POSTGRES_DB='test_db',
        POSTGRES_HOST='localhost',
        POSTGRES_PORT=5432,
        STORAGE_TYPE='local',
        MAX_FILE_SIZE=1024 * 1024,  # 1MB
        FASTAPI_BASE_URL='http://localhost:8000',
        DJANGO_SECRET_KEY='test-secret-key-for-testing',
    )


@pytest.fixture
def test_client() -> TestClient:
    """Test client."""
    return TestClient(app)


@pytest.fixture
def sample_file_content() -> bytes:
    """Sample file content."""
    return b'test file content'


@pytest.fixture
def sample_large_file_content() -> bytes:
    """Sample large file content."""
    return b'x' * (256 * 1024)  # 256KB


@pytest.fixture
def sample_file_record() -> FileRecord:
    """Sample file record."""
    return FileRecord(
        file_id='12345678-1234-5678-1234-567812345679',
        filename='test_file.txt',
        content_type='text/plain',
        size=1024,
        user_id=1,
        account_id=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Mock HTTP client."""
    mock = AsyncMock()
    mock.check_file_permission.return_value = True
    return mock


@pytest.fixture
def mock_storage_service():
    """Mock storage service."""
    mock = AsyncMock()

    # get_storage_path - synchronous method, not AsyncMock
    mock.get_storage_path = Mock(
        return_value=(
            'test-bucket',
            '12345678-1234-5678-1234-567812345678',
        ),
    )
    return mock


@pytest.fixture
def mock_repository():
    """Mock file repository."""
    return AsyncMock()


@pytest_asyncio.fixture
async def mcp_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    await engine.dispose()


@pytest.fixture
def mcp_context(
    mocker: MockerFixture,
    mcp_session: AsyncSession,
    root_path: str = '',
) -> Generator[dict[str, Any]]:
    settings = BaseAppSettings(
        MCP_ENABLED=True,
        MCP_FILE_SERVICE_SECRET='test-file-secret-for-storage-only-1234',
        FASTAPI_BASE_URL='https://app.example/files',
    )
    mocker.patch(
        'src.shared_kernel.auth.mcp.get_settings', return_value=settings
    )
    mocker.patch(
        'src.presentation.api.mcp_files.get_settings', return_value=settings
    )
    record = FileRecord(
        file_id='file-123',
        size=8,
        content_type='text/plain',
        filename='a.txt',
        user_id=1,
        account_id=10,
        created_at=datetime.now(UTC),
    )
    state = {
        'active': True,
        'user_id': 1,
        'account_id': 10,
        'connection_id': 'conn-1',
        'authorization_id': 'authorization-1',
        'expires_at': int(datetime.now(UTC).timestamp()) + 600,
    }
    callbacks = []

    async def core_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path == '/internal/mcp/complete-upload':
            callbacks.append(dict(body))
            return {
                'id': body['upload_session_id'],
                'status': 'ready',
                'file_id': body['file_id'],
            }
        if body.get('credential') in {
            'mcp-d_bad-scope',
            'mcp-d_revoked',
            'bad',
            'ordinary',
        }:
            return {'active': False}
        if body.get('upload_session_id') not in (None, 'session-1'):
            return {'active': False}
        grant = {**state, 'operation': body['operation']}
        if body['operation'] in ('upload', 'import'):
            grant['upload_session_id'] = 'session-1'
        return grant

    core = mocker.patch(
        'src.shared_kernel.auth.mcp.MCPCoreClient.post',
        side_effect=core_post,
    )
    ordinary = mocker.patch(
        'src.shared_kernel.auth.token_auth.PneumaticToken.data',
        return_value={'user_id': 1, 'account_id': 10},
    )
    storage = AsyncMock()
    storage.get_storage_path = Mock(return_value=('bucket', 'path'))
    events = AsyncMock()
    download = AsyncMock()
    download.get_metadata.return_value = record

    async def get_stream(
        *,
        file_record: FileRecord,
        range_header: str | None,
    ):
        return iter([b'cd' if range_header == 'bytes=2-3' else b'abcdefgh'])

    download.get_stream.side_effect = get_stream
    permission = AsyncMock()
    application = FastAPI(root_path=root_path)
    application.add_middleware(AuthenticationMiddleware, require_auth=True)
    application.add_middleware(SecurityHeadersMiddleware)
    register_exception_handlers(application)
    application.include_router(mcp_router)
    application.include_router(files_router)

    async def session_dep() -> AsyncIterator[AsyncSession]:
        yield mcp_session

    async def storage_dep() -> AsyncIterator[AsyncMock]:
        yield storage

    application.dependency_overrides.update(
        {
            get_db_session: session_dep,
            get_storage_service: storage_dep,
            get_settings_dep: lambda: settings,
            get_download_use_case: lambda: download,
            get_http_client: lambda: permission,
            get_request_events: lambda: events,
        }
    )
    with TestClient(application) as client:
        yield {
            'client': client,
            'state': state,
            'core': core,
            'ordinary': ordinary,
            'session': mcp_session,
            'record': record,
            'settings': settings,
            'storage': storage,
            'events': events,
            'callbacks': callbacks,
            'download': download,
            'permission': permission,
        }


@pytest.fixture
def root_mcp_context(
    mocker: MockerFixture,
    mcp_session: AsyncSession,
) -> Generator[dict[str, Any]]:
    yield from mcp_context.__wrapped__(
        mocker=mocker, mcp_session=mcp_session, root_path='/files'
    )


@pytest.fixture
def pg_upload(
    mocker: MockerFixture,
) -> tuple[BaseAppSettings, AuthUser, AsyncMock]:
    settings = BaseAppSettings(FASTAPI_BASE_URL='https://example.com/files')
    grant = FileGrant(
        active=True,
        user_id=1,
        account_id=10,
        connection_id='conn-1',
        operation='upload',
        upload_session_id='session-1',
    )
    mocker.patch(
        'src.shared_kernel.auth.mcp.MCPCoreClient.validate', return_value=grant
    )
    storage = AsyncMock()
    storage.get_storage_path = Mock(return_value=('bucket', 'object'))
    return settings, grant.user(credential='mcp-u_upload'), storage


@pytest.fixture(scope='module')
def core_metadata() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[3]
        / 'backend/src/storage/file_metadata.py'
    )
    if not path.is_file():
        pytest.skip(
            'The shared backend checkout is required for contract tests'
        )
    # Load the actual pure function from the shared checkout. Importing the
    # whole backend module would bind its Django package to storage's `src`
    # namespace; storage intentionally does not depend on Django.
    source = ast.parse(path.read_text(encoding='utf-8'))
    constants = ast.parse(
        path.with_name('constants.py').read_text(encoding='utf-8'),
    )
    isolated = ast.Module(
        body=[
            node
            for node in constants.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == 'UNNAMED_FILE'
                for target in node.targets
            )
        ]
        + [
            node
            for node in source.body
            if (isinstance(node, ast.Import) and node.names[0].name == 're')
            or (
                isinstance(node, ast.FunctionDef)
                and node.name == 'canonical_filename'
            )
        ],
        type_ignores=[],
    )
    module = ModuleType('core_file_metadata')
    exec(compile(isolated, str(path), 'exec'), module.__dict__)  # noqa: S102
    return module


@pytest.fixture
def mcp_upload_request() -> Callable[..., Any]:
    def _upload(
        context: dict[str, Any],
        content: bytes = b'abc',
        session: str = 'session-1',
    ):
        return context['client'].post(
            url='/upload',
            headers={
                'Authorization': 'Bearer mcp-u_upload',
                'X-MCP-Upload-Session': session,
            },
            files={'file': ('a.txt', content, 'text/plain')},
        )

    return _upload


@pytest.fixture
def mcp_import_request() -> Callable[..., Any]:
    def _import(
        context: dict[str, Any],
        secret: str | None = None,
    ):
        return context['client'].post(
            url='/internal/mcp/import',
            headers={
                'Authorization': 'Bearer '
                + (
                    context[
                        'settings'
                    ].MCP_FILE_SERVICE_SECRET.get_secret_value()
                    if secret is None
                    else secret
                )
            },
            json={
                'credential': 'mcp-u_import',
                'upload_session_id': 'session-1',
                'url': 'https://example.com/file?signature=secret',
                'filename': 'a.txt',
            },
        )

    return _import


@pytest.fixture
def age_mcp_upload() -> Callable[..., Any]:
    async def _age(context: dict[str, Any]) -> str:
        file_id = str(uuid5(NAMESPACE_URL, 'pneumatic:mcp:session-1'))
        context['session'].add(
            instance=FileRecordORM(
                file_id=file_id,
                user_id=1,
                account_id=10,
                filename='a.txt',
                content_type='text/plain',
                size=3,
                created_at=datetime.now(UTC) - timedelta(hours=25),
            ),
        )
        context['session'].add(
            instance=MCPUploadORM(
                session_id='session-1',
                connection_id='conn-1',
                user_id=1,
                account_id=10,
                file_id=file_id,
                fingerprint='fixture-not-an-upload',
            ),
        )
        await context['session'].commit()
        return file_id

    return _age


@pytest.fixture
def mcp_cleanup_request() -> Callable[..., Any]:
    def _cleanup(
        context: dict[str, Any],
        secret: str | None = None,
    ):
        return context['client'].post(
            url='/internal/mcp/cleanup',
            headers={
                'Authorization': 'Bearer '
                + (
                    context[
                        'settings'
                    ].MCP_FILE_SERVICE_SECRET.get_secret_value()
                    if secret is None
                    else secret
                ),
            },
        )

    return _cleanup


@pytest.fixture
def create_mcp_orphan() -> Callable[..., Any]:
    async def _orphan(context: dict[str, Any]) -> str:
        file_id = str(uuid5(NAMESPACE_URL, 'pneumatic:mcp:session-1'))
        context['session'].add(
            instance=MCPUploadAttemptORM(
                session_id='session-1',
                connection_id='conn-1',
                user_id=1,
                account_id=10,
                file_id=file_id,
                created_at=datetime.now(UTC) - timedelta(hours=25),
            )
        )
        await context['session'].commit()
        return file_id

    return _orphan


@pytest.fixture
def mcp_service(mcp_context: dict[str, Any]) -> MCPUploadService:
    """A real transaction service over the request's isolated ORM session."""
    return MCPUploadService(
        session=mcp_context['session'],
        storage=mcp_context['storage'],
        settings=mcp_context['settings'],
    )


@pytest.fixture
def mcp_user(mcp_context: dict[str, Any]) -> AuthUser:
    """A concrete session owner carrying its core delegation provenance."""
    return FileGrant(
        **mcp_context['state'],
        operation='upload',
        upload_session_id='session-1',
    ).user(credential='mcp-u_upload')


@pytest.fixture
def mcp_command() -> UploadFileCommand:
    """Real stream and metadata; each test owns its command."""
    return UploadFileCommand(
        file_stream=BytesIO(b'abc'),
        filename='a.txt',
        content_type='text/plain',
        size=3,
        user_id=1,
        account_id=10,
    )


@pytest.fixture
def mcp_settings() -> Callable[..., BaseAppSettings]:
    def _settings(**kwargs: Any) -> BaseAppSettings:
        return BaseAppSettings(
            _env_file=None,
            DJANGO_SECRET_KEY='test-key',
            MCP_ENABLED=True,
            MCP_FILE_SERVICE_SECRET='x' * 32,
            **kwargs,
        )

    return _settings


@pytest.fixture
def mcp_read_headers() -> dict[str, str]:
    """A read delegation, never an ordinary account credential."""
    return {'Authorization': 'Bearer mcp-d_read'}


@pytest_asyncio.fixture
async def mcp_ticket(mcp_context: dict[str, Any]) -> str:
    """Create a real hashed ticket without exercising unrelated endpoints."""
    token = 't' * 43
    mcp_context['session'].add(
        instance=FileRecordORM(
            file_id='file-123',
            size=8,
            filename='a.txt',
            content_type='text/plain',
            user_id=1,
            account_id=10,
        )
    )
    await mcp_context['session'].flush()
    mcp_context['session'].add(
        instance=MCPDownloadTicketORM(
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            connection_id='conn-1',
            authorization_id='authorization-1',
            user_id=1,
            account_id=10,
            file_id='file-123',
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    await mcp_context['session'].commit()
    return token


@pytest.fixture
def mcp_cleanup_candidates() -> Callable[..., Any]:
    async def seed(
        context: dict[str, Any],
        orphan_count: int,
        upload_count: int,
    ) -> list[Any]:
        oldest = datetime.now(UTC) - timedelta(hours=26)
        expected_calls = []
        for index in range(orphan_count + upload_count):
            session_id = str(uuid5(NAMESPACE_URL, f'cleanup-session:{index}'))
            file_id = str(
                uuid5(NAMESPACE_URL, f'pneumatic:mcp:{session_id}'),
            )
            timestamp = oldest + timedelta(seconds=index)
            if index < orphan_count:
                context['session'].add(
                    instance=MCPUploadAttemptORM(
                        session_id=session_id,
                        connection_id='conn-1',
                        user_id=1,
                        account_id=10,
                        file_id=file_id,
                        created_at=timestamp,
                    ),
                )
            else:
                context['session'].add(
                    instance=FileRecordORM(
                        file_id=file_id,
                        user_id=1,
                        account_id=10,
                        size=3,
                        created_at=timestamp,
                    ),
                )
                context['session'].add(
                    instance=MCPUploadORM(
                        session_id=session_id,
                        connection_id='conn-1',
                        user_id=1,
                        account_id=10,
                        file_id=file_id,
                        fingerprint='fixture-not-an-upload',
                    ),
                )
            expected_calls.append(
                call(
                    path='/internal/mcp/cleanup-upload',
                    body={
                        'upload_session_id': session_id,
                        'file_id': file_id,
                        'account_id': 10,
                        'user_id': 1,
                    },
                ),
            )
        await context['session'].commit()
        return expected_calls

    return seed
