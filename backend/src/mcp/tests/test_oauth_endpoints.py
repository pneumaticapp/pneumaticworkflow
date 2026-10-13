from collections.abc import Callable
from datetime import timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from django.utils import timezone
from oauth2_provider import models as oauth_models
from oauth2_provider.models import AccessToken, Application, RefreshToken
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from redis.exceptions import ConnectionError as RedisConnectionError
from rest_framework.test import APIClient

from src.authentication.services.delegation import DelegationService
from src.generics.tests.clients import PneumaticApiClient
from src.mcp.enums import McpScope
from src.authentication.exceptions import (
    InvalidMcpToken,
)
from src.mcp.models import (
    AccessBinding,
    AuthorizationRequest,
    ClientPolicy,
    LoginCode,
    RefreshBinding,
)
from src.authentication.tokens import get_digest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('auth_method', ['none', 'client_secret_basic'])
def test_oauth_rate__registration_within_budget__real_client(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    auth_method: str,
):
    # arrange
    metadata = {
        'client_name': 'Bounded DCR',
        'redirect_uris': ['https://client.test/callback'],
        'grant_types': ['authorization_code', 'refresh_token'],
        'response_types': ['code'],
        'token_endpoint_auth_method': auth_method,
    }

    # act
    response = api_client.post(
        path='/oauth/mcp/register',
        data=metadata,
        format='json',
        REMOTE_ADDR=oauth_rate.ip,
    )
    application = Application.objects.get(
        client_id=response.json()['client_id'],
    )

    # assert
    assert response.status_code == 201
    assert ClientPolicy.objects.filter(application=application).exists()
    assert AccessToken.objects.filter(application=application).count() == 1
    assert oauth_rate.backend.get(oauth_rate.keys['register']) == 1000
    if auth_method == 'client_secret_basic':
        assert application.client_secret != response.json()['client_secret']


def test_oauth_rate__registration_exhausted__no_hash_or_rows(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    mocker: MockerFixture,
):
    # arrange
    oauth_rate.backend.set(oauth_rate.keys['register'], 943, 60)
    hashing = mocker.spy(obj=oauth_models, name='make_password')
    counts = (
        Application.objects.count(),
        AccessToken.objects.count(),
        ClientPolicy.objects.count(),
    )

    # act
    response = api_client.post(
        path='/oauth/mcp/register',
        data={
            'redirect_uris': ['https://client.test/callback'],
            'token_endpoint_auth_method': 'client_secret_basic',
        },
        format='json',
        REMOTE_ADDR=oauth_rate.ip,
    )

    # assert
    assert response.status_code == 429
    assert response.json() == {
        'error': 'temporarily_unavailable',
        'error_description': 'Too many authorization requests.',
    }
    assert response['Cache-Control'] == 'no-store'
    assert response['Referrer-Policy'] == 'no-referrer'
    assert 1 <= int(response['Retry-After']) <= 3
    assert (
        Application.objects.count(),
        AccessToken.objects.count(),
        ClientPolicy.objects.count(),
    ) == counts
    hashing.assert_not_called()


@pytest.mark.parametrize('method', ['GET', 'HEAD'])
@pytest.mark.parametrize('path', ['authorize', 'login'])
@pytest.mark.parametrize('suffix', ['', '/'])
def test_oauth_rate__authorize_login_shared_budget__no_state_change(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    authorization_parameters: dict,
    login_code: dict,
    method: str,
    path: str,
    suffix: str,
):
    # arrange
    first = api_client.get(
        path='/oauth/mcp/authorize',
        data=authorization_parameters,
        REMOTE_ADDR=oauth_rate.ip,
    )
    count = AuthorizationRequest.objects.count()
    data = authorization_parameters if path == 'authorize' else login_code
    code = LoginCode.objects.get(
        authorization_request_id=login_code['request_id'],
    )

    # act
    response = getattr(api_client, method.lower())(
        path=f'/oauth/mcp/{path}{suffix}',
        data=data,
        REMOTE_ADDR=oauth_rate.ip,
    )
    code.refresh_from_db()
    auth_request = AuthorizationRequest.objects.get(
        pk=code.authorization_request_id,
    )

    # assert
    assert first.status_code == 302
    assert response.status_code == 429
    assert response['Cache-Control'] == 'no-store'
    assert int(response['Retry-After']) > 0
    assert AuthorizationRequest.objects.count() == count
    assert code.consumed_at is None
    assert auth_request.login_completed_at is None
    assert oauth_rate.backend.get(oauth_rate.keys['authorize']) == 1000
    if method == 'HEAD':
        assert response.content == b''
    else:
        assert response.json()['error'] == 'temporarily_unavailable'


def test_oauth_rate__refresh_within_budget__real_token_rotation(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    grant: SimpleNamespace,
):
    # arrange
    refresh = RefreshToken.objects.create(
        token='rate-refresh',
        application=grant.app,
        user=grant.user,
        access_token=grant.access,
    )
    RefreshBinding.objects.create(
        refresh_token=refresh,
        connection=grant.connection,
    )

    # act
    response = api_client.post(
        path='/oauth/mcp/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh.token,
            'client_id': grant.app.client_id,
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
        format='multipart',
        REMOTE_ADDR=oauth_rate.ip,
    )

    # assert
    assert response.status_code == 200, response.content
    assert AccessBinding.objects.filter(
        access_token__token_checksum=get_digest(
            value=response.json()['access_token'],
        ),
        connection=grant.connection,
    ).exists()
    assert RefreshBinding.objects.filter(
        refresh_token__token_checksum=get_digest(
            value=response.json()['refresh_token'],
        ),
        connection=grant.connection,
    ).exists()
    assert oauth_rate.backend.get(oauth_rate.keys['token']) == 1000


@pytest.mark.parametrize('path', ['token', 'revoke'])
def test_oauth_rate__token_budget_exhausted__preserves_grant(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    grant: SimpleNamespace,
    path: str,
):
    # arrange
    oauth_rate.backend.set(oauth_rate.keys['token'], 943, 60)
    refresh = RefreshToken.objects.create(
        token='bounded-refresh',
        application=grant.app,
        user=grant.user,
        access_token=grant.access,
    )
    RefreshBinding.objects.create(
        refresh_token=refresh,
        connection=grant.connection,
    )
    counts = AccessToken.objects.count(), RefreshToken.objects.count()

    # act
    response = api_client.post(
        path=f'/oauth/mcp/{path}',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh.token,
            'client_id': grant.app.client_id,
            'token': grant.token,
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
        format='multipart',
        REMOTE_ADDR=oauth_rate.ip,
    )
    grant.connection.refresh_from_db()
    refresh.refresh_from_db()

    # assert
    assert response.status_code == 429
    assert response['Cache-Control'] == 'no-store'
    assert (
        AccessToken.objects.count(),
        RefreshToken.objects.count(),
    ) == counts
    assert grant.connection.revoked_at is None
    assert refresh.revoked is None
    assert AccessToken.objects.filter(pk=grant.access.pk).exists()


def test_oauth_rate__redis_outage__sanitized_before_sdk(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mocker: MockerFixture,
    mcp_settings: SettingsWrapper,
):
    # arrange
    transport = mocker.patch.object(
        target=oauth_rate.backend,
        attribute='get',
        side_effect=RedisConnectionError('private Redis address'),
    )
    count = Application.objects.count()

    # act
    response = api_client.post(
        path='/oauth/mcp/register',
        data={},
        REMOTE_ADDR=oauth_rate.ip,
    )

    # assert
    assert response.status_code == 503
    assert response.json() == {
        'error': 'temporarily_unavailable',
        'error_description': (
            'Authorization service is temporarily unavailable.'
        ),
    }
    assert response['Cache-Control'] == 'no-store'
    assert response['Retry-After'] == '5'
    assert Application.objects.count() == count
    transport.assert_called_once_with(oauth_rate.keys['register'], None)


def test_oauth_rate__disabled_feature__no_cache_access(
    api_client: PneumaticApiClient,
    oauth_rate: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    mocker: MockerFixture,
):
    # arrange
    mcp_settings.MCP_ENABLED = False
    transport = mocker.spy(obj=oauth_rate.backend, name='get')

    # act
    response = api_client.post(path='/oauth/mcp/register', data={})

    # assert
    assert response.status_code == 404
    transport.assert_not_called()


@pytest.mark.parametrize(
    'kind,expired',
    [
        ('access_token', False),
        ('access_token', True),
        ('refresh_token', False),
    ],
)
def test_oauth_revoke__bound_token__revokes_connection(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    kind: str,
    expired: bool,
):
    # arrange
    refresh = RefreshToken.objects.create(
        token='revoke-refresh-token',
        application=grant.app,
        user=grant.user,
        access_token=grant.access,
    )
    RefreshBinding.objects.create(
        refresh_token=refresh,
        connection=grant.connection,
    )
    delegated = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='list_templates',
        method='GET',
        path='/templates',
    )
    if expired:
        grant.access.expires = timezone.now() - timedelta(seconds=1)
        grant.access.save(update_fields=['expires'])
    token = refresh.token if kind == 'refresh_token' else grant.token
    data = {'client_id': grant.app.client_id, 'token': token}
    if kind == 'refresh_token':
        data['token_type_hint'] = kind

    # act
    response = api_client.post(
        path='/oauth/mcp/revoke',
        data=data,
        format='multipart',
    )
    grant.connection.refresh_from_db()
    # assert
    assert response.status_code == 200
    assert response.content == b''
    assert grant.connection.revoked_at is not None
    assert not AccessToken.objects.filter(pk=grant.access.pk).exists()
    assert not RefreshToken.objects.filter(
        pk=refresh.pk,
        revoked__isnull=True,
    ).exists()
    with pytest.raises(InvalidMcpToken):
        DelegationService.get_delegation(credential=delegated.credential)


@pytest.mark.parametrize('kind', ['access_token', 'refresh_token'])
def test_oauth_revoke__foreign_client__preserves_grant(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    kind: str,
):
    # arrange
    refresh = RefreshToken.objects.create(
        token='foreign-refresh-token',
        application=grant.app,
        user=grant.user,
        access_token=grant.access,
    )
    RefreshBinding.objects.create(
        refresh_token=refresh,
        connection=grant.connection,
    )
    other_client = Application.objects.create(
        name='Other revoke client',
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
    )
    token = refresh.token if kind == 'refresh_token' else grant.token

    # act
    response = api_client.post(
        path='/oauth/mcp/revoke',
        data={
            'client_id': other_client.client_id,
            'token': token,
            'token_type_hint': kind,
        },
        format='multipart',
    )
    grant.connection.refresh_from_db()
    refresh.refresh_from_db()
    binding = DelegationService.get_access_binding(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
    )

    # assert
    assert response.status_code == 200
    assert response.content == b''
    assert grant.connection.revoked_at is None
    assert refresh.revoked is None
    assert binding.connection_id == grant.connection.pk
    assert AccessToken.objects.filter(pk=grant.access.pk).exists()


def test_oauth_revoke__unknown_token__successful_noop(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
):
    # arrange
    data = {'client_id': grant.app.client_id, 'token': 'unknown-token'}

    # act
    response = api_client.post(
        path='/oauth/mcp/revoke',
        data=data,
        format='multipart',
    )
    grant.connection.refresh_from_db()

    # assert
    assert response.status_code == 200
    assert response.content == b''
    assert grant.connection.revoked_at is None
    assert AccessToken.objects.filter(pk=grant.access.pk).exists()


def test_oauth_revoke__disabled_client__protocol_denial(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
):
    # arrange
    ClientPolicy.objects.filter(application=grant.app).update(is_active=False)

    # act
    response = api_client.post(
        path='/oauth/mcp/revoke',
        data={'client_id': grant.app.client_id, 'token': grant.token},
        format='multipart',
    )
    grant.connection.refresh_from_db()

    # assert
    assert response.status_code == 401
    assert response.json()['error'] == 'invalid_client'
    assert grant.connection.revoked_at is None
    assert AccessToken.objects.filter(pk=grant.access.pk).exists()


@pytest.mark.parametrize(
    'path',
    [
        '/.well-known/oauth-protected-resource',
        '/.well-known/oauth-protected-resource/mcp',
    ],
)
def test_resource_metadata__public_alias__exact_contract(
    api_client: PneumaticApiClient,
    mcp_settings: SettingsWrapper,
    path: str,
):
    # arrange
    expected = {
        'resource': mcp_settings.MCP_PUBLIC_URL,
        'authorization_servers': [mcp_settings.MCP_ISSUER_URL],
        'scopes_supported': [
            McpScope.READ,
            McpScope.WRITE,
            McpScope.FILE_READ,
            McpScope.FILE_WRITE,
        ],
        'bearer_methods_supported': ['header'],
    }

    # act
    response = api_client.get(path=path)

    # assert
    assert response.status_code == 200
    assert response.json() == expected
    assert response['Cache-Control'] == 'no-store'
    assert response['Referrer-Policy'] == 'no-referrer'


def test_server_metadata__public_endpoint__exact_contract(
    api_client: PneumaticApiClient,
    mcp_settings: SettingsWrapper,
):
    # arrange
    issuer = mcp_settings.MCP_ISSUER_URL
    expected = {
        'issuer': issuer,
        'authorization_endpoint': f'{issuer}/oauth/mcp/authorize',
        'token_endpoint': f'{issuer}/oauth/mcp/token',
        'registration_endpoint': f'{issuer}/oauth/mcp/register',
        'revocation_endpoint': f'{issuer}/oauth/mcp/revoke',
        'response_types_supported': ['code'],
        'grant_types_supported': ['authorization_code', 'refresh_token'],
        'code_challenge_methods_supported': ['S256'],
        'token_endpoint_auth_methods_supported': [
            'none',
            'client_secret_basic',
        ],
        'scopes_supported': [
            McpScope.READ,
            McpScope.WRITE,
            McpScope.FILE_READ,
            McpScope.FILE_WRITE,
        ],
        'client_id_metadata_document_supported': True,
        'authorization_response_iss_parameter_supported': True,
    }

    # act
    response = api_client.get(path='/.well-known/oauth-authorization-server')

    # assert
    assert response.status_code == 200
    assert response.json() == expected
    assert response['Cache-Control'] == 'no-store'


@pytest.mark.parametrize(
    'path',
    [
        '/.well-known/oauth-protected-resource',
        '/.well-known/oauth-protected-resource/mcp',
        '/.well-known/oauth-authorization-server',
    ],
)
def test_metadata__disabled_mcp__not_found(
    api_client: PneumaticApiClient,
    mcp_settings: SettingsWrapper,
    path: str,
):
    # arrange
    mcp_settings.MCP_ENABLED = False

    # act
    response = api_client.get(path=path)

    # assert
    assert response.status_code == 404


def test_registration__csrf_enforced_public_origin__valid(
    mcp_settings: SettingsWrapper,
):
    # arrange
    client = APIClient(enforce_csrf_checks=True)
    metadata = {
        'client_name': 'External MCP',
        'redirect_uris': ['https://client.test/callback'],
        'grant_types': ['authorization_code', 'refresh_token'],
        'response_types': ['code'],
        'token_endpoint_auth_method': 'none',
    }

    # act
    response = client.post(
        path='/oauth/mcp/register',
        data=metadata,
        format='json',
    )

    # assert
    assert response.status_code == 201
    assert response.json()['registration_client_uri'] == (
        f'{mcp_settings.MCP_ISSUER_URL}/oauth/mcp/register/'
        + response.json()['client_id']
    )
    assert (
        ClientPolicy.objects.get(
            application__client_id=response.json()['client_id'],
        ).can_introspect
        is False
    )


@pytest.mark.parametrize(
    'case,status',
    [
        ('read', 200),
        ('update', 200),
        ('invalid', 400),
        ('delete', 204),
    ],
)
def test_registration_management__authorized_operation__expected_status(
    registered_client: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    case: str,
    status: int,
):
    # arrange
    client = registered_client.client
    metadata = registered_client.metadata
    path = registered_client.path

    # act
    if case == 'read':
        response = client.get(path=path)
    elif case == 'update':
        response = client.put(path=path, data=metadata, format='json')
    elif case == 'invalid':
        response = client.put(
            path=path,
            data={**metadata, 'grant_types': ['password']},
            format='json',
        )
    else:
        response = client.delete(path=path)

    # assert
    assert response.status_code == status
    if status == 200:
        assert response.json()['registration_client_uri'] == (
            mcp_settings.MCP_ISSUER_URL + path
        )
    elif status == 400:
        assert response.json() == {'error': 'invalid_client_metadata'}
    else:
        assert not Application.objects.filter(
            client_id=registered_client.registered['client_id'],
        ).exists()


@pytest.mark.parametrize(
    'field,value',
    [
        ('grant_types', None),
        ('grant_types', [{}]),
        ('response_types', None),
        ('token_endpoint_auth_method', {}),
        ('client_name', []),
    ],
)
def test_registration__malformed_metadata__400(
    api_client: PneumaticApiClient,
    field: str,
    value: Any,
):
    # arrange
    data = {
        'redirect_uris': ['https://client.test/callback'],
        field: value,
    }

    # act
    response = api_client.post(path='/oauth/mcp/register', data=data)

    # assert
    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_client_metadata'


@pytest.mark.parametrize(
    'operation,status,error',
    [
        ('token', 400, 'invalid_grant'),
        ('revoke', 401, 'invalid_client'),
    ],
)
def test_protocol_posts__csrf_enforced__oauth_error(
    mcp_settings: SettingsWrapper,
    operation: str,
    status: int,
    error: str,
):
    # arrange
    client = APIClient(enforce_csrf_checks=True)
    data = {
        'grant_type': 'authorization_code',
        'code': 'wrong',
        'resource': mcp_settings.MCP_PUBLIC_URL,
        'token': 'wrong',
        'client_id': 'wrong',
    }

    # act
    response = client.post(
        path=f'/oauth/mcp/{operation}',
        data=data,
        format='multipart',
    )

    # assert
    assert response.status_code == status
    assert response.json()['error'] == error


def test_disabled_client__private_introspection__inactive(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    ClientPolicy.objects.filter(application=grant.app).update(is_active=False)
    api_client.credentials(
        HTTP_X_MCP_SERVICE_SECRET=mcp_settings.MCP_SERVICE_SECRET,
    )

    # act
    response = api_client.post(
        path='/internal/mcp/introspect',
        data={
            'token': grant.token,
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
    )

    # assert
    assert response.status_code == 200, response.content
    assert response.json() == {'active': False}


def test_introspection__full_middleware__positive_identity(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    api_client.credentials(
        HTTP_X_MCP_SERVICE_SECRET=mcp_settings.MCP_SERVICE_SECRET,
    )

    # act
    response = api_client.post(
        path='/internal/mcp/introspect',
        data={
            'token': grant.token,
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
    )

    # assert
    assert response.status_code == 200, response.content
    assert response.json()['active'] is True
    assert response.json()['connection_id'] == str(grant.connection.pk)
    assert 'file_service_auth' not in response.cookies


def test_delegation__full_middleware__no_browser_capability_cookie(
    grant: SimpleNamespace,
    delegated_client: Callable,
):
    # arrange
    client = delegated_client(
        tool='list_templates',
        method='GET',
        path='/templates',
    )

    # act
    response = client.get(path='/templates')

    # assert
    assert response.status_code == 200, response.content
    assert 'file_service_auth' not in response.cookies
