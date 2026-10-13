import src.authentication.messages as auth_messages
import base64
import hashlib
from collections.abc import Callable
from datetime import timedelta
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from django.utils import timezone
from django.utils.functional import Promise
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from src.authentication.enums import AuthTokenType
from src.generics.tests.clients import PneumaticApiClient
from src.mcp.models import (
    AccessBinding,
    AuthorizationRequest,
    Connection,
)
from src.authentication.services.connections import ConnectionService
from src.processes.models.templates.template import TemplateIntegrations
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('login_complete', [False, True])
def test_consent_context__live_request__bound_identity(
    api_client: PneumaticApiClient,
    authorization_request: AuthorizationRequest,
    grant: SimpleNamespace,
    login_complete: bool,
):

    # arrange
    if login_complete:
        authorization_request.user = grant.user
        authorization_request.account = grant.account
        authorization_request.login_completed_at = timezone.now()
        authorization_request.save(
            update_fields=['user', 'account', 'login_completed_at'],
        )
    api_client.token_authenticate(user=grant.user)
    expected = {
        'request_id': str(authorization_request.pk),
        'client': {'id': grant.app.client_id, 'name': grant.app.name},
        'client_id': grant.app.client_id,
        'client_name': grant.app.name,
        'account': {'id': grant.account.pk, 'name': grant.account.name},
        'user_id': grant.user.pk,
        'account_id': grant.account.pk,
        'scopes': grant.connection.scopes,
        'expires_at': authorization_request.expires_at.isoformat(),
        'login_complete': login_complete,
    }

    # act
    response = api_client.get(
        path='/integrations/mcp/consent',
        data={'request_id': str(authorization_request.pk)},
    )
    authorization_request.refresh_from_db()

    # assert
    assert response.status_code == 200
    assert response.json() == expected
    assert authorization_request.user_id == grant.user.pk
    assert authorization_request.account_id == grant.account.pk
    assert response['Cache-Control'] == 'no-store'
    assert response['Referrer-Policy'] == 'no-referrer'


@pytest.mark.parametrize(
    'case,status,message',
    [
        ('missing', 404, auth_messages.MSG_AU_0021),
        ('foreign_user', 404, auth_messages.MSG_AU_0021),
        ('foreign_account', 404, auth_messages.MSG_AU_0021),
        ('expired', 410, auth_messages.MSG_AU_0022),
        ('consumed', 410, auth_messages.MSG_AU_0022),
    ],
)
def test_consent_context__unavailable_request__denied(
    api_client: PneumaticApiClient,
    authorization_request: AuthorizationRequest,
    grant: SimpleNamespace,
    case: str,
    status: int,
    message: str | Promise,
):

    # arrange
    request_id = str(authorization_request.pk)
    if case == 'missing':
        authorization_request.delete()
    elif case == 'foreign_user':
        authorization_request.user = create_test_not_admin(
            account=grant.account,
        )
        authorization_request.account = grant.account
        authorization_request.save(update_fields=['user', 'account'])
    elif case == 'foreign_account':
        other_account = create_test_account()
        authorization_request.user = create_test_owner(
            account=other_account,
            email='other-owner@pneumatic.app',
        )
        authorization_request.account = other_account
        authorization_request.save(update_fields=['user', 'account'])
    elif case == 'expired':
        authorization_request.expires_at = timezone.now() - timedelta(
            seconds=1,
        )
        authorization_request.save(update_fields=['expires_at'])
    else:
        authorization_request.consumed_at = timezone.now()
        authorization_request.save(update_fields=['consumed_at'])
    api_client.token_authenticate(user=grant.user)

    # act
    response = api_client.get(
        path='/integrations/mcp/consent',
        data={'request_id': request_id},
    )

    # assert
    assert response.status_code == status
    assert response.json() == {'detail': message}


@pytest.mark.parametrize(
    'data,reason',
    [
        ({}, 'This field is required.'),
        ({'request_id': ''}, 'Must be a valid UUID.'),
        ({'request_id': 'undefined'}, 'Must be a valid UUID.'),
        ({'request_id': 123}, 'Must be a valid UUID.'),
    ],
)
def test_consent_context__invalid_query__standard_error(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    data: dict,
    reason: str,
):

    # arrange
    api_client.token_authenticate(user=grant.user)

    # act
    response = api_client.get(path='/integrations/mcp/consent', data=data)

    # assert
    assert response.status_code == 400
    assert response.json() == {
        'message': reason,
        'code': 'validation_error',
        'details': {'name': 'request_id', 'reason': reason},
    }


@pytest.mark.parametrize(
    'endpoint',
    ['/integrations/mcp/consent', '/integrations/mcp/connections'],
)
def test_browser_mcp__anonymous__requires_login(
    api_client: PneumaticApiClient,
    endpoint: str,
):

    # arrange
    expected = {'detail': NotAuthenticated.default_detail}

    # act
    response = api_client.get(path=endpoint)

    # assert
    assert response.status_code == 401
    assert response.json() == expected


@pytest.mark.parametrize(
    'endpoint',
    ['/integrations/mcp/consent', '/integrations/mcp/connections'],
)
def test_browser_mcp__api_key__requires_user_login(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    endpoint: str,
):

    # arrange
    api_client.token_authenticate(
        user=grant.user,
        token_type=AuthTokenType.API,
    )

    # act
    response = api_client.get(path=endpoint)

    # assert
    assert response.status_code == 401
    assert response.json() == {'detail': 'A user login token is required.'}


@pytest.mark.parametrize('empty', [False, True])
def test_connections__user_login__scoped_response(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    empty: bool,
):

    # arrange
    expected = {
        'results': [
            {
                'id': str(grant.connection.pk),
                'client_id': grant.app.client_id,
                'client_name': grant.app.name,
                'scopes': grant.connection.scopes,
                'created_at': grant.connection.created_at.isoformat(),
                'revoked_at': None,
                'user_id': grant.user.pk,
                'account_id': grant.account.pk,
            },
        ],
    }
    if empty:
        grant.connection.delete()
        expected = {'results': []}
    api_client.token_authenticate(user=grant.user)

    # act
    response = api_client.get(path='/integrations/mcp/connections')

    # assert
    assert response.status_code == 200
    assert response.json() == expected
    assert response['Cache-Control'] == 'no-store'


def test_connections_revoke__foreign_account__404(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
):

    # arrange
    other = create_test_owner(
        account=create_test_account(),
        email='foreign-revoke@test.com',
    )
    api_client.token_authenticate(user=other)

    # act
    response = api_client.delete(
        path=f'/integrations/mcp/connections/{grant.connection.pk}',
    )

    # assert
    assert response.status_code == 404
    grant.connection.refresh_from_db()
    assert grant.connection.revoked_at is None


def test_upload_status__anonymous__401(
    api_client: PneumaticApiClient,
    upload_session: SimpleNamespace,
):

    # arrange
    path = f'/integrations/mcp/uploads/{upload_session.session.pk}'

    # act
    response = api_client.get(path=path)

    # assert
    assert response.status_code == 401
    assert response.json() == {
        'detail': NotAuthenticated.default_detail,
    }


def test_upload_status__foreign_account__404(
    grant: SimpleNamespace,
    upload_session: SimpleNamespace,
    api_client: PneumaticApiClient,
):

    # arrange
    other_account = create_test_account()
    other = create_test_owner(
        account=other_account,
        email='foreign-upload@test.com',
    )
    api_client.token_authenticate(user=other)
    path = f'/integrations/mcp/uploads/{upload_session.session.pk}'

    # act
    response = api_client.get(path=path)

    # assert
    assert response.status_code == 404
    upload_session.session.refresh_from_db()
    assert upload_session.session.connection_id == grant.connection.pk


@pytest.mark.parametrize(
    'endpoint,field',
    [
        ('/internal/mcp/introspect', 'resource'),
        ('/internal/mcp/delegate', 'tool'),
        ('/internal/mcp/validate-files', 'file_id'),
        ('/internal/mcp/complete-upload', 'upload_session_id'),
        ('/internal/mcp/cleanup-upload', 'upload_session_id'),
        ('/integrations/mcp/login-code', 'request_id'),
        ('/integrations/mcp/consent', 'request_id'),
        ('/integrations/mcp/uploads', 'size'),
    ],
)
def test_mcp_request__null_field__standard_validation_error(
    api_client: PneumaticApiClient,
    delegated_client: Callable,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    endpoint: str,
    field: str,
):

    # arrange
    data = {
        'token': grant.token,
        'resource': mcp_settings.MCP_PUBLIC_URL,
        'tool': 'list_templates',
        'method': 'GET',
        'path': '/templates',
        'credential': 'test-credential',
        'operation': 'metadata',
        'file_id': 'test-file',
        'upload_session_id': '11111111-1111-1111-1111-111111111111',
        'account_id': grant.account.pk,
        'user_id': grant.user.pk,
        'name': 'test.txt',
        'size': 3,
        'content_type': 'text/plain',
        'request_id': '11111111-1111-1111-1111-111111111111',
        'allow': True,
        'task_id': 1,
        'field_api_name': 'file',
        'filename': 'test.txt',
    }
    data[field] = None
    if endpoint.startswith('/internal/mcp/'):
        api_client.credentials(
            HTTP_X_MCP_SERVICE_SECRET=mcp_settings.MCP_SERVICE_SECRET,
            HTTP_X_MCP_FILE_SERVICE_SECRET=(
                mcp_settings.MCP_FILE_SERVICE_SECRET
            ),
        )
    elif endpoint == '/integrations/mcp/uploads':
        api_client = delegated_client(
            tool='create_upload_link',
            method='POST',
            path=endpoint,
        )
    else:
        api_client.token_authenticate(user=grant.user)
    reason = 'This field may not be null.'

    # act
    response = api_client.post(
        path=endpoint,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.json() == {
        'message': reason,
        'code': 'validation_error',
        'details': {'name': field, 'reason': reason},
    }


@pytest.mark.parametrize(
    'value,reason',
    [
        (None, 'This field may not be null.'),
        ('', 'This field may not be blank.'),
        ({}, 'Not a valid string.'),
    ],
)
def test_introspection__invalid_token__standard_validation_error(
    api_client: PneumaticApiClient,
    mcp_settings: SettingsWrapper,
    value: Any,
    reason: str,
):

    # arrange
    api_client.credentials(
        HTTP_X_MCP_SERVICE_SECRET=mcp_settings.MCP_SERVICE_SECRET,
    )

    # act
    response = api_client.post(
        path='/internal/mcp/introspect',
        data={'token': value, 'resource': mcp_settings.MCP_PUBLIC_URL},
    )

    # assert
    assert response.status_code == 400
    assert response.json() == {
        'message': reason,
        'code': 'validation_error',
        'details': {'name': 'token', 'reason': reason},
    }


@pytest.mark.parametrize(
    'header,path',
    [
        ('HTTP_X_MCP_SERVICE_SECRET', '/internal/mcp/introspect'),
        ('HTTP_X_MCP_FILE_SERVICE_SECRET', '/internal/mcp/validate-files'),
        ('HTTP_AUTHORIZATION', '/internal/mcp/validate-files'),
    ],
)
def test_service_auth__non_ascii_header__401(
    api_client: PneumaticApiClient,
    header: str,
    path: str,
):
    # arrange
    supplied = 'Bearer é' if header == 'HTTP_AUTHORIZATION' else 'é'
    api_client.credentials(**{header: supplied})

    # act
    response = api_client.post(path=path, data={})

    # assert
    assert response.status_code == 401, response.content
    assert response.json()['code'] == 'service_auth_failed'


@pytest.mark.parametrize(
    'valid_service,expected_code',
    [
        (False, 'service_auth_failed'),
        (True, 'invalid_token'),
    ],
)
def test_delegate__invalid_credentials__distinct_code(
    api_client: PneumaticApiClient,
    mcp_settings: SettingsWrapper,
    valid_service: bool,
    expected_code: str,
):

    # arrange
    data = {
        'token': 'invalid-token',
        'resource': mcp_settings.MCP_PUBLIC_URL,
        'tool': 'list_templates',
        'method': 'GET',
        'path': '/templates',
    }
    if valid_service:
        api_client.credentials(
            HTTP_X_MCP_SERVICE_SECRET=mcp_settings.MCP_SERVICE_SECRET,
        )

    # act
    response = api_client.post(path='/internal/mcp/delegate', data=data)

    # assert
    assert response.status_code == 401
    assert response.json()['code'] == expected_code


def test_run__legacy_connection_alias__ordinary_write_and_group_revocation(
    grant: SimpleNamespace,
    delegated_client: Callable,
):
    # arrange
    template = create_test_template(user=grant.user, is_active=True)
    TemplateIntegrations.objects.create(
        template=template,
        account=grant.account,
    )
    path = f'/templates/{template.pk}/run'
    client = delegated_client(tool='run_workflow', method='POST', path=path)
    first = client.post(path=path, data={})
    alias = Connection.objects.create(
        user=grant.user,
        account=grant.account,
        application=grant.app,
        resource=grant.connection.resource,
        scopes=grant.connection.scopes,
    )
    AccessBinding.objects.filter(access_token=grant.access).update(
        connection=alias,
    )
    client = delegated_client(tool='run_workflow', method='POST', path=path)

    # act
    replay = client.post(path=path, data={})
    ConnectionService.revoke(connection=alias)
    grant.connection.refresh_from_db()
    alias.refresh_from_db()

    # assert
    assert first.status_code == 200, first.content
    assert replay.status_code == 200, replay.content
    assert template.workflows.count() == 2
    assert grant.connection.revoked_at is not None
    assert alias.revoked_at is not None


def test_ordinary_login__file_cookie__unchanged(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
):
    # arrange
    api_client.token_authenticate(user=grant.user)

    # act
    response = api_client.get(path='/accounts/user')

    # assert
    assert response.status_code == 200, response.content
    assert 'file_service_auth' in response.cookies
    assert response.cookies['file_service_auth']['max-age'] == 86400


def test_comment__repeated_request__creates_each_comment(
    delegated_client: Callable,
    task_field: TaskField,
):
    # arrange
    path = f'/workflows/{task_field.workflow_id}/comment'
    client = delegated_client(
        tool='add_workflow_comment',
        method='POST',
        path=path,
    )
    payload = {'text': 'HTTP comment'}

    # act
    response = client.post(
        path=path,
        data=payload,
    )
    replay = client.post(
        path=path,
        data=payload,
    )

    # assert
    assert response.status_code == 200, response.content
    assert replay.status_code == 200, replay.content
    assert replay.json()['id'] != response.json()['id']


def test_introspection__user_token_not_service__401(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
):
    # arrange
    api_client.token_authenticate(user=grant.user)

    # act
    response = api_client.post(
        path='/internal/mcp/introspect',
        data={'token': grant.token, 'resource': 'wrong'},
    )

    # assert
    assert response.status_code == 401


@pytest.mark.parametrize(
    'method,path',
    [
        ('GET', '/accounts/user'),
        ('POST', '/templates'),
    ],
)
def test_delegation__different_route_and_method__default_deny(
    delegated_client: Callable,
    method: str,
    path: str,
):

    # arrange
    client = delegated_client(
        tool='list_templates',
        method='GET',
        path='/templates',
    )

    # act
    response = client.generic(method=method, path=path)

    # assert
    assert response.status_code == 403
    assert response.json()['detail'] == PermissionDenied.default_detail


def test_delegation__public_custom_auth_endpoint__denied(
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
    response = client.post(path='/auth/signin', data={})

    # assert
    assert response.status_code == 403


def test_run__repeated_payload__creates_each_workflow(
    grant: SimpleNamespace,
    delegated_client: Callable,
):
    # arrange
    template = create_test_template(user=grant.user, is_active=True)
    TemplateIntegrations.objects.create(
        template=template,
        account=grant.account,
    )
    path = f'/templates/{template.pk}/run'
    client = delegated_client(tool='run_workflow', method='POST', path=path)
    data = {'name': 'MCP run', 'kickoff': {}}

    # act
    first = client.post(path=path, data=data)
    second = client.post(path=path, data=data)

    # assert
    assert first.status_code == 200, first.content
    assert second.status_code == 200, second.content
    assert second.json()['id'] != first.json()['id']
    assert template.workflows.count() == 2


def test_run__different_payload__creates_each_workflow(
    grant: SimpleNamespace,
    delegated_client: Callable,
):
    # arrange
    template = create_test_template(user=grant.user, is_active=True)
    TemplateIntegrations.objects.create(
        template=template,
        account=grant.account,
    )
    path = f'/templates/{template.pk}/run'
    client = delegated_client(tool='run_workflow', method='POST', path=path)

    client.post(
        path=path,
        data={'name': 'One'},
    )
    # act
    second = client.post(
        path=path,
        data={'name': 'Two'},
    )

    # assert
    assert second.status_code == 200, second.content
    assert template.workflows.count() == 2


def test_oauth__bridge_consent_code_pkce__bound_connection(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    verifier = 'v' * 64
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip('=')
    )
    params = {
        'client_id': grant.app.client_id,
        'redirect_uri': 'https://client.test/callback',
        'response_type': 'code',
        'scope': 'pneumatic:read',
        'state': 'client-state',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'resource': mcp_settings.MCP_PUBLIC_URL,
    }

    # act
    authorization = api_client.get(path='/oauth/mcp/authorize', data=params)
    request_id = parse_qs(urlparse(authorization['Location']).query)[
        'request_id'
    ][0]
    api_client.token_authenticate(user=grant.user)
    login_code = api_client.post(
        path='/integrations/mcp/login-code',
        data={'request_id': request_id},
    )
    handoff = api_client.get(path='/oauth/mcp/login', data=login_code.json())
    consent = api_client.post(
        path='/integrations/mcp/consent',
        data={'request_id': request_id, 'allow': True},
    )
    final = api_client.get(path='/oauth/mcp/login', data=consent.json())
    code = parse_qs(urlparse(final['Location']).query)['code'][0]
    api_client.credentials()
    token = api_client.post(
        path='/oauth/mcp/token',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': grant.app.client_id,
            'redirect_uri': params['redirect_uri'],
            'code_verifier': verifier,
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
        format='multipart',
    )

    # assert
    assert authorization.status_code == 302
    assert handoff.status_code == 302
    assert consent.status_code == 200, consent.content
    assert final.status_code == 302
    assert token.status_code == 200, token.content
    assert token.json()['expires_in'] == 900
    assert Connection.objects.filter(user=grant.user).count() == 1
