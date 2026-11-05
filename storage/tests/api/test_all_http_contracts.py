"""Every Files operation and declared status exercised through real ASGI."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import jwt
import pytest
from botocore.exceptions import ClientError
from starlette.testclient import TestClient

from src.application.use_cases import DownloadFileUseCase, UploadFileUseCase
from src.infra.adapters.storage_service import StorageService
from src.infra.http_client import HttpClient
from src.infra.repositories import FileRecordRepository
from src.main import app
from src.shared_kernel.di import (
    get_download_use_case,
    get_http_client,
    get_settings_dep,
    get_upload_use_case,
)
from src.shared_kernel.exceptions import (
    DatabaseConstraintError,
    DatabaseOperationError,
    RedisConnectionError,
)
from src.shared_kernel.middleware.rate_limit import (
    RateLimitMiddleware,
    _RateLimit,
    _SlidingWindow,
)
from src.shared_kernel.uow import UnitOfWork
from tests.contracts import FilesContract

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest_mock import MockerFixture

    from src.domain.entities import FileRecord
    from src.shared_kernel.config import BaseAppSettings


@dataclass(frozen=True)
class Scenario:
    """Expected public outcome of one real request pipeline."""

    name: str
    method: str
    status: int
    code: str | None = None


SCENARIOS = (
    Scenario('upload', 'POST', 200),
    Scenario('upload_empty_filename', 'POST', 200),
    Scenario('upload_missing_boundary', 'POST', 400),
    Scenario('upload_no_auth', 'POST', 401, 'AUTH_001'),
    Scenario('upload_invalid_auth', 'POST', 401, 'AUTH_001'),
    Scenario('upload_conflict', 'POST', 409, 'DB_004'),
    Scenario('upload_too_large', 'POST', 413, 'FILE_003'),
    Scenario('upload_missing_file', 'POST', 422, 'VAL_002'),
    Scenario('upload_wrong_form_type', 'POST', 422, 'VAL_002'),
    Scenario('upload_content_type_name', 'POST', 422, 'VAL_002'),
    Scenario('upload_rate_limit', 'POST', 429),
    Scenario('upload_database_error', 'POST', 500, 'DB_002'),
    Scenario('upload_auth_backend_error', 'POST', 500, 'INFRA_005'),
    Scenario('upload_storage_error', 'POST', 503, 'STORAGE_002'),
    Scenario('download', 'GET', 200),
    Scenario('download_range', 'GET', 206),
    Scenario('download_login_redirect', 'GET', 302),
    Scenario('download_error_redirect', 'GET', 302),
    Scenario('download_no_auth', 'GET', 401, 'AUTH_001'),
    Scenario('download_denied', 'GET', 403, 'FILE_002'),
    Scenario('download_missing_metadata', 'GET', 404, 'FILE_001'),
    Scenario('download_missing_storage', 'GET', 404, 'STORAGE_005'),
    Scenario('download_unsatisfiable', 'GET', 416),
    Scenario('download_invalid_id', 'GET', 422, 'VAL_002'),
    Scenario('download_rate_limit', 'GET', 429),
    Scenario('download_database_error', 'GET', 500, 'DB_002'),
    Scenario('download_auth_backend_error', 'GET', 500, 'INFRA_005'),
    Scenario('download_core_unavailable', 'GET', 502, 'EXT_003'),
    Scenario('download_storage_error', 'GET', 503, 'STORAGE_003'),
    Scenario('download_invalid_range', 'GET', 503, 'STORAGE_003'),
    Scenario('download_core_timeout', 'GET', 504, 'EXT_004'),
)


@pytest.fixture(scope='module')
def files_contract(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[FilesContract]:
    """Require all documented outcomes when the complete matrix is selected."""
    contract = FilesContract(app.openapi())
    yield contract
    selected = {
        item.callspec.params['case'].name
        for item in request.session.items
        if item.module is request.module
        and hasattr(item, 'callspec')
        and isinstance(item.callspec.params.get('case'), Scenario)
    }
    complete = selected == {case.name for case in SCENARIOS}
    if complete:
        contract.assert_complete()
    report = contract.report()
    report['complete_matrix_selected'] = complete
    target = os.environ.get('FILES_CONTRACT_REPORT')
    destination = (
        Path(target)
        if target
        else tmp_path_factory.getbasetemp() / 'files-contract-coverage.json'
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding='utf-8')


@pytest.fixture
def files_contract_client(
    files_contract: FilesContract,
) -> Generator[TestClient]:
    """Apply shared assertions to every actual HTTP exchange in a scenario."""
    client = TestClient(
        app, raise_server_exceptions=False, follow_redirects=False
    )
    send = client.send

    def checked_send(request: httpx.Request, **kwargs: Any) -> httpx.Response:
        request.read()
        response = send(request, **kwargs)
        files_contract.exchange(response)
        return response

    client.send = checked_send
    yield client
    client.close()


@dataclass
class Pipeline:
    """Real use cases/adapters with storage/cache/DB/Core I/O replaced."""

    repository: AsyncMock
    s3: AsyncMock
    transport: AsyncMock
    redis: AsyncMock
    record: FileRecord
    settings: BaseAppSettings
    body: MagicMock


@pytest.fixture
def file_pipeline(
    mocker: MockerFixture,
    test_settings: BaseAppSettings,
    sample_file_record: FileRecord,
) -> Pipeline:
    test_settings.MAX_FILE_SIZE = 1024
    test_settings.BUCKET_PREFIX = 'contracts'
    test_settings.FRONTEND_URL = 'https://app.example.test'
    for module in (
        'src.infra.adapters.storage_service',
        'src.shared_kernel.browser_utils',
        'src.shared_kernel.exceptions.exception_handler',
        'src.shared_kernel.auth.guest_token',
    ):
        mocker.patch(f'{module}.get_settings', return_value=test_settings)
    redis = mocker.patch(
        'src.shared_kernel.auth.redis_client.RedisAuthClient.get',
        new_callable=AsyncMock,
        return_value={'user_id': 1, 'account_id': 1},
    )
    repository = AsyncMock(spec=FileRecordRepository)
    record = replace(sample_file_record, size=4)
    repository.get_by_id.return_value = record
    storage = StorageService()
    s3 = AsyncMock()
    storage._s3_client = s3
    body = MagicMock()
    body.iter_chunks.return_value.__aiter__.return_value = [b'abcd']
    s3.get_object.return_value = {'Body': body}
    session = MagicMock()
    session.begin.return_value.__aenter__ = AsyncMock()
    session.begin.return_value.__aexit__ = AsyncMock(return_value=False)
    upload = UploadFileUseCase(
        file_repository=repository,
        storage_service=storage,
        unit_of_work=UnitOfWork(session),
        fastapi_base_url='http://testserver/files',
    )
    download = DownloadFileUseCase(repository, storage)
    transport = AsyncMock(spec=httpx.AsyncClient)
    transport.post.return_value = httpx.Response(204)
    mocker.patch(
        'src.infra.http_client.get_shared_client', return_value=transport
    )
    http_client = HttpClient('http://core.test/attachments/check-permission')
    mocker.patch.dict(
        app.dependency_overrides,
        {
            get_upload_use_case: lambda: upload,
            get_download_use_case: lambda: download,
            get_http_client: lambda: http_client,
            get_settings_dep: lambda: test_settings,
        },
    )
    return Pipeline(
        repository, s3, transport, redis, record, test_settings, body
    )


def enable_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable the actual middleware with isolated windows for this test."""
    if app.middleware_stack is None:
        app.middleware_stack = app.build_middleware_stack()
    middleware = app.middleware_stack
    while not isinstance(middleware, RateLimitMiddleware):
        middleware = middleware.app
    monkeypatch.setattr(middleware, '_enabled', True)
    monkeypatch.setattr(middleware, '_windows', defaultdict(_SlidingWindow))
    monkeypatch.setattr(
        middleware,
        '_limits',
        {
            'upload': _RateLimit(1, 60),
            'download': _RateLimit(1, 60),
        },
    )


def storage_error(code: str) -> ClientError:
    return ClientError(
        {'Error': {'Code': code, 'Message': 'Unavailable'}},
        'ContractTransport',
    )


def configure_failures(name: str, pipeline: Pipeline) -> None:
    """Replace failures only at their persistence/network boundaries."""
    failures = {
        'upload_conflict': (
            pipeline.repository.create,
            DatabaseConstraintError('files_pkey'),
        ),
        'upload_database_error': (
            pipeline.repository.create,
            DatabaseOperationError('insert'),
        ),
        'upload_storage_error': (
            pipeline.s3.upload_fileobj,
            storage_error('AccessDenied'),
        ),
        'download_missing_storage': (
            pipeline.s3.get_object,
            storage_error('NoSuchKey'),
        ),
        'download_database_error': (
            pipeline.repository.get_by_id,
            DatabaseOperationError('select'),
        ),
        'download_core_unavailable': (
            pipeline.transport.post,
            httpx.ConnectError('Offline'),
        ),
        'download_core_timeout': (
            pipeline.transport.post,
            httpx.ReadTimeout('Timeout'),
        ),
        'download_storage_error': (
            pipeline.s3.get_object,
            storage_error('InvalidRange'),
        ),
        'download_invalid_range': (
            pipeline.s3.get_object,
            storage_error('InvalidRange'),
        ),
    }
    if name in failures:
        boundary, error = failures[name]
        boundary.side_effect = error


def configure_record(name: str, pipeline: Pipeline) -> None:
    """Arrange record/transport values consumed by real application logic."""
    if name in {
        'download_denied',
        'download_core_unavailable',
        'download_core_timeout',
    }:
        pipeline.repository.get_by_id.return_value = replace(
            pipeline.record,
            user_id=2,
        )
    if name == 'download_denied':
        pipeline.transport.post.return_value = httpx.Response(403)
    if name in {'download_missing_metadata', 'download_error_redirect'}:
        pipeline.repository.get_by_id.return_value = None
    if name == 'download_range':
        pipeline.body.iter_chunks.return_value.__aiter__.return_value = [b'bc']


def configure(
    case: Scenario,
    pipeline: Pipeline,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, str]:
    """Arrange transport outcomes without replacing handlers or responses."""
    headers = {
        'Authorization': 'Bearer contract-token',
        'Accept': 'application/json',
    }
    name = case.name
    if 'no_auth' in name or name == 'download_login_redirect':
        headers.pop('Authorization')
    if name == 'upload_invalid_auth':
        pipeline.redis.return_value = None
    if 'auth_backend_error' in name:
        pipeline.redis.side_effect = RedisConnectionError('Cache unavailable')
    if name == 'upload_too_large':
        pipeline.settings.MAX_FILE_SIZE = 3
    ranges = {
        'download_invalid_range': 'invalid-range',
        'download_unsatisfiable': 'bytes=9-',
        'download_range': 'bytes=1-2',
    }
    if name in ranges:
        headers['Range'] = ranges[name]
    if name.endswith('_redirect'):
        headers['Accept'] = 'text/html'
    if name.endswith('_rate_limit'):
        enable_rate_limit(monkeypatch)
    configure_failures(name, pipeline)
    configure_record(name, pipeline)
    return headers


def upload_options(name: str, headers: dict[str, str]) -> dict[str, Any]:
    """Encode invalid forms and an UploadFile with a present empty name."""
    bodies = {
        'upload_missing_file': {},
        'upload_wrong_form_type': {'data': {'file': 'not-an-upload'}},
        'upload_missing_boundary': {'content': b'invalid multipart bytes'},
        'upload_content_type_name': {
            'content': (
                b'--contract\r\n'
                b'Content-Disposition: form-data; name="file"\r\n'
                b'Content-Type: application/octet-stream; '
                b'name="not-a-file.bin"\r\n\r\ndata\r\n--contract--\r\n'
            ),
        },
        'upload_empty_filename': {
            'content': (
                b'--contract\r\n'
                b'Content-Disposition: form-data; name="file"; filename=""'
                b'\r\nContent-Type: text/plain\r\n\r\n'
                b'data\r\n--contract--\r\n'
            ),
        },
    }
    if name == 'upload_missing_boundary':
        headers['Content-Type'] = 'multipart/form-data'
    elif name in {'upload_empty_filename', 'upload_content_type_name'}:
        headers['Content-Type'] = 'multipart/form-data; boundary=contract'
    body = bodies.get(
        name, {'files': {'file': ('contract.txt', b'abcd', 'text/plain')}}
    )
    return {'headers': headers, **body}


def assert_upload_details(
    case: Scenario, pipeline: Pipeline, response: httpx.Response
) -> None:
    """Verify the real parser and filename fallback, beyond the JSON shape."""
    if case.name == 'upload_missing_boundary':
        assert response.json() == {'detail': 'Missing boundary in multipart.'}
        documented = app.openapi()['paths']['/files/upload']['post'][
            'responses'
        ]['400']['content']['application/json']
        assert documented['example'] == response.json()
        pipeline.redis.assert_awaited_once()
        pipeline.repository.create.assert_not_awaited()
        pipeline.s3.upload_fileobj.assert_not_awaited()
    elif case.name == 'upload_content_type_name':
        pipeline.redis.assert_awaited_once()
        pipeline.repository.create.assert_not_awaited()
        pipeline.s3.upload_fileobj.assert_not_awaited()
    elif case.name == 'upload_empty_filename':
        record = pipeline.repository.create.await_args.args[0]
        assert record.filename == 'unnamed_file'
        assert record.size == len(b'data')
        assert record.user_id == record.account_id == 1
        pipeline.redis.assert_awaited_once()
        pipeline.s3.upload_fileobj.assert_awaited_once()


@pytest.mark.parametrize('case', SCENARIOS, ids=lambda case: case.name)
def test_all_operations__documented_outcome__matches_contract(
    case: Scenario,
    file_pipeline: Pipeline,
    files_contract_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = configure(case, file_pipeline, monkeypatch)
    path = (
        '/upload'
        if case.method == 'POST'
        else (
            '/'
            + (
                'x' * 513
                if case.name == 'download_invalid_id'
                else file_pipeline.record.file_id
            )
        )
    )
    options = (
        upload_options(case.name, headers)
        if case.method == 'POST'
        else {'headers': headers}
    )
    if case.name.endswith('_rate_limit'):
        initial = files_contract_client.request(case.method, path, **options)
        assert initial.status_code == 200
    response = files_contract_client.request(case.method, path, **options)
    assert response.status_code == case.status
    assert_upload_details(case, file_pipeline, response)
    if case.code:
        assert response.json()['code'] == case.code
    if case.name == 'download':
        assert response.content == b'abcd'
    if case.name == 'download_range':
        assert response.content == b'bc'
        assert response.headers['Content-Range'] == 'bytes 1-2/4'
    if case.name == 'download_login_redirect':
        assert response.headers['Location'].startswith(
            'https://app.example.test/auth/signin/?redirectUrl=',
        )
    if case.name == 'download_error_redirect':
        assert (
            response.headers['Location'] == 'https://app.example.test/error/'
        )
    if case.status == 416:
        assert response.headers['Content-Range'] == 'bytes */4'
    if case.name == 'download_invalid_range':
        assert 'Content-Range' not in response.headers


@pytest.mark.parametrize('method', ['POST', 'GET'])
@pytest.mark.parametrize(
    'credential',
    [
        'bearer',
        'X-Guest-Authorization',
        'X-Public-Authorization',
        'file_service_auth',
        'token',
        'guest-token',
        'public-token',
    ],
)
def test_all_credentials__real_middleware__contract(
    method: str,
    credential: str,
    file_pipeline: Pipeline,
    files_contract_client: TestClient,
) -> None:
    token = 'contract-token'
    if credential in {'X-Guest-Authorization', 'guest-token'}:
        token = jwt.encode(
            {'user_id': 1, 'account_id': 1},
            file_pipeline.settings.DJANGO_SECRET_KEY,
            algorithm='HS256',
        )
    if credential in {'X-Public-Authorization', 'public-token'}:
        token = 'Token abcdefgh'
        file_pipeline.repository.get_by_id.return_value = replace(
            file_pipeline.record,
            user_id=None,
        )
    headers = {'Accept': 'application/json'}
    if credential == 'bearer':
        headers['Authorization'] = f'Bearer {token}'
    elif credential.startswith('X-'):
        headers[credential] = token
    else:
        files_contract_client.cookies.set(credential, token)
    if method == 'POST':
        response = files_contract_client.post(
            '/upload',
            headers=headers,
            files={'file': ('contract.txt', b'abcd', 'text/plain')},
        )
    else:
        response = files_contract_client.get(
            f'/{file_pipeline.record.file_id}',
            headers=headers,
        )
    assert response.status_code == 200
