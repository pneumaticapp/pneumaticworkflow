"""Check the documented contracts against file API behavior."""

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from src.application.use_cases import DownloadFileUseCase
from src.infra.adapters.storage_service import StorageService
from src.infra.repositories import FileRecordRepository
from src.main import app
from src.presentation.openapi import FileErrorResponse
from src.shared_kernel.di import get_download_use_case
from src.shared_kernel.middleware.auth_middleware import (
    AuthenticationMiddleware,
)


def test_openapi__all_file_operations__covered():
    # arrange
    expected = {
        (f'/files{route.path}', method.lower())
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }

    # act
    schema = app.openapi()
    actual = {
        (path, method)
        for path, item in schema['paths'].items()
        for method in item
    }

    # assert
    assert actual == expected


def test_openapi__download_metadata__preserves_route_response_class():
    """Binary documentation must not replace the original route default."""
    route = next(
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == '/{file_id}'
    )
    response_class = getattr(
        route.response_class,
        'value',
        route.response_class,
    )
    assert response_class is JSONResponse


def test_openapi__security__matches_middleware_credentials():
    # arrange
    middleware = AuthenticationMiddleware(app)
    schema = app.openapi()
    schemes = schema['components']['securitySchemes']
    expected = {
        (source, name)
        for name, source, _authenticate in middleware.auth_strategies
    }

    # act
    documented = {
        ('bearer', 'Authorization')
        if scheme['type'] == 'http'
        else (scheme['in'], scheme['name'])
        for scheme in schemes.values()
    }
    alternatives = {name for choice in schema['security'] for name in choice}

    # assert
    assert documented == expected
    assert alternatives == set(schemes)
    assert all(len(choice) == 1 for choice in schema['security'])


@pytest.mark.parametrize('status', ['200', '206'])
def test_openapi__download__binary_response_and_headers(status):
    # arrange
    operation = app.openapi()['paths']['/files/{file_id}']['get']

    # act
    response = operation['responses'][status]

    # assert
    assert 'application/json' not in response['content']
    assert response['content']['*/*']['schema'] == {
        'type': 'string',
        'format': 'binary',
    }
    assert {'Content-Disposition', 'Content-Length', 'Accept-Ranges'} <= (
        response['headers'].keys()
    )
    if status == '206':
        assert 'Content-Range' in response['headers']


def test_openapi__download__range_and_browser_responses():
    # arrange
    operation = app.openapi()['paths']['/files/{file_id}']['get']

    # act
    responses = operation['responses']
    range_parameter = next(
        parameter
        for parameter in operation['parameters']
        if parameter['name'] == 'Range'
    )

    # assert
    assert range_parameter['in'] == 'header'
    assert not range_parameter['required']
    assert 'content' not in responses['416']
    assert 'Content-Range' in responses['416']['headers']
    assert 'Location' in responses['302']['headers']


@pytest.mark.parametrize(
    ('path', 'method', 'expected'),
    [
        (
            '/files/upload',
            'post',
            {'401', '403', '409', '413', '422', '429', '500', '503'},
        ),
        (
            '/files/{file_id}',
            'get',
            {'401', '403', '404', '422', '429', '500', '502', '503', '504'},
        ),
    ],
)
def test_openapi__file_errors__documented(path, method, expected):
    # act
    responses = app.openapi()['paths'][path][method]['responses']

    # assert
    assert expected <= responses.keys()
    assert responses['422']['content']['application/json']['schema'] == {
        '$ref': '#/components/schemas/FileErrorResponse',
    }
    assert responses['429']['content']['application/json']['schema'] == {
        '$ref': '#/components/schemas/FileRateLimitResponse',
    }
    assert 'Retry-After' in responses['429']['headers']


def test_openapi__validation_error__matches_actual_body(
    e2e_client,
    mock_auth_middleware,
    mock_storage_service,
    auth_headers,
):
    # arrange
    documented = app.openapi()['components']['schemas']['FileErrorResponse']

    # act
    response = e2e_client.post('/upload', headers=auth_headers)
    error = FileErrorResponse.model_validate(response.json())

    # assert
    assert response.status_code == 422
    assert set(documented['required']) == {'code', 'message'}
    assert set(response.json()) == {'code', 'message', 'details'}
    assert error.code == 'VAL_002'
    assert error.details is not None
    assert error.details.reason


@pytest.fixture
def download_storage_pipeline(
    mocker,
    mock_auth_middleware,
    test_settings,
    sample_file_record,
):
    """Keep the endpoint, use case and adapter real; replace I/O only."""
    test_settings.BUCKET_PREFIX = 'docs-range'
    mocker.patch(
        'src.infra.adapters.storage_service.get_settings',
        return_value=test_settings,
    )
    repository = AsyncMock(spec=FileRecordRepository)
    repository.get_by_id.return_value = sample_file_record
    s3 = AsyncMock()
    storage = StorageService()
    storage._s3_client = s3  # Replace only the S3 transport.
    use_case = DownloadFileUseCase(
        file_repository=repository,
        storage_service=storage,
    )
    mocker.patch.dict(
        app.dependency_overrides,
        {get_download_use_case: lambda: use_case},
    )
    return repository, s3, sample_file_record


@pytest.mark.parametrize(
    ('range_header', 'storage_error'),
    [
        ('bytes=9999-', 'InvalidRange'),
        ('not-a-range', 'InvalidArgument'),
    ],
)
def test_download__storage_rejects_range__documented_503(
    e2e_client,
    download_storage_pipeline,
    auth_headers,
    range_header,
    storage_error,
):
    # arrange
    repository, s3, record = download_storage_pipeline
    s3.get_object.side_effect = ClientError(
        {'Error': {'Code': storage_error, 'Message': 'Rejected Range'}},
        'GetObject',
    )
    operation = app.openapi()['paths']['/files/{file_id}']['get']
    range_parameter = next(
        parameter
        for parameter in operation['parameters']
        if parameter['name'] == 'Range'
    )

    # act
    response = e2e_client.get(
        f'/{record.file_id}',
        headers={
            **auth_headers,
            'Range': range_header,
            'Accept': 'application/json',
        },
    )

    # assert
    assert response.status_code == 503
    assert response.json()['code'] == 'STORAGE_003'
    assert 'Content-Range' not in response.headers
    repository.get_by_id.assert_awaited_once_with(record.file_id)
    s3.get_object.assert_awaited_once_with(
        Bucket='docs-range-1',
        Key=record.file_id,
        Range=range_header,
    )
    assert 'STORAGE_003' in operation['responses']['503']['description']
    assert 'STORAGE_003' in range_parameter['description']
    assert (
        'not a guaranteed response'
        in (operation['responses']['416']['description'])
    )


def test_download__storage_accepts_range_beyond_metadata__local_416(
    e2e_client,
    download_storage_pipeline,
    auth_headers,
):
    # arrange
    _repository, s3, record = download_storage_pipeline
    s3.get_object.return_value = {'Body': MagicMock()}

    # act
    response = e2e_client.get(
        f'/{record.file_id}',
        headers={
            **auth_headers,
            'Range': 'bytes=9999-',
            'Accept': 'application/json',
        },
    )

    # assert
    assert response.status_code == 416
    assert response.content == b''
    assert response.headers['Content-Range'] == f'bytes */{record.size}'
    s3.get_object.assert_awaited_once_with(
        Bucket='docs-range-1',
        Key=record.file_id,
        Range='bytes=9999-',
    )


@pytest.mark.parametrize(
    'content_type',
    [
        'application/pdf',
        'text/plain',
        'image/jpeg',
    ],
)
@pytest.mark.parametrize(
    ('range_header', 'status'),
    [
        (None, 200),
        ('bytes=0-3', 206),
    ],
)
def test_download__stored_mime_type__covered_by_schema(
    e2e_client: TestClient,
    download_storage_pipeline: tuple,
    auth_headers: dict[str, str],
    content_type: str,
    range_header: str | None,
    status: int,
) -> None:
    # arrange
    repository, s3, record = download_storage_pipeline
    record = replace(record, content_type=content_type, size=4)
    repository.get_by_id.return_value = record
    body = MagicMock()
    body.iter_chunks.return_value.__aiter__.return_value = [b'test']
    s3.get_object.return_value = {'Body': body}
    headers = {**auth_headers, 'Accept': 'application/json'}
    if range_header:
        headers['Range'] = range_header

    # act
    response = e2e_client.get(f'/{record.file_id}', headers=headers)
    contract = app.openapi()['paths']['/files/{file_id}']['get']['responses'][
        str(status)
    ]

    # assert
    assert response.status_code == status
    assert response.headers['Content-Type'].split(';')[0] == content_type
    assert response.content == b'test'
    assert contract['content']['*/*']['schema'] == {
        'type': 'string',
        'format': 'binary',
    }
    body.close.assert_called_once()
