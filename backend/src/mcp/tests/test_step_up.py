import base64
import hashlib
from collections.abc import Callable
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import PermissionDenied

from src.authentication.services.delegation import DelegationService
from src.generics.tests.clients import PneumaticApiClient
from src.mcp.models import Connection
from src.processes.models.workflows.fields import TaskField

pytestmark = pytest.mark.django_db


def test_consent__step_up_upload_connection__same_identity_strict_tokens(
    api_client: PneumaticApiClient,
    delegated_client: Callable,
    grant: SimpleNamespace,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
):
    # arrange
    grant.access.scope = 'files:write'
    grant.access.save(update_fields=['scope'])
    grant.connection.scopes = ['files:write']
    grant.connection.save(update_fields=['scopes'])
    client = delegated_client(
        tool='create_upload_link',
        method='POST',
        path='/integrations/mcp/uploads',
    )
    created = client.post(
        path='/integrations/mcp/uploads',
        data={
            'target_type': 'task',
            'task_id': task_field.task_id,
            'field_api_name': task_field.api_name,
            'filename': 'test.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    upload = created.json()
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {mcp_settings.MCP_FILE_SERVICE_SECRET}',
    )
    completed = api_client.post(
        path='/internal/mcp/complete-upload',
        data={
            'credential': upload['credential'],
            'upload_session_id': upload['id'],
            'file_id': 'step-up-file-1',
            'name': 'test.txt',
            'size': 3,
            'content_type': 'text/plain',
        },
    )
    verifier = 'v' * 64
    challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest(),
        )
        .decode()
        .rstrip('=')
    )
    params = {
        'client_id': grant.app.client_id,
        'redirect_uri': 'https://client.test/callback',
        'response_type': 'code',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'scope': 'pneumatic:write files:read files:write',
        'resource': mcp_settings.MCP_PUBLIC_URL,
    }
    api_client.credentials()

    # act
    authorization = api_client.get(path='/oauth/mcp/authorize', data=params)
    request_id = parse_qs(urlparse(authorization['Location']).query)[
        'request_id'
    ][0]
    api_client.token_authenticate(user=grant.user)
    login_code = api_client.post(
        path='/integrations/mcp/login-code',
        data={
            'request_id': request_id,
        },
    )
    api_client.get(path='/oauth/mcp/login', data=login_code.json())
    consent = api_client.post(
        path='/integrations/mcp/consent',
        data={
            'request_id': request_id,
            'allow': True,
        },
    )
    final = api_client.get(path='/oauth/mcp/login', data=consent.json())
    code = parse_qs(urlparse(final['Location']).query)['code'][0]
    api_client.credentials()
    exchanged = api_client.post(
        path='/oauth/mcp/token',
        data={
            **params,
            'grant_type': 'authorization_code',
            'code': code,
            'code_verifier': verifier,
        },
        format='multipart',
    )
    new_token = exchanged.json()['access_token']
    status_path = f'/integrations/mcp/uploads/{upload["id"]}'
    poll_grant = DelegationService.create(
        token=new_token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='get_upload_status',
        method='GET',
        path=status_path,
    )
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {poll_grant.credential}',
    )
    polled = api_client.get(path=status_path)
    attach_path = status_path + '/attach'
    attach_grant = DelegationService.create(
        token=new_token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='attach_uploaded_file',
        method='POST',
        path=attach_path,
    )
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {attach_grant.credential}',
    )
    attached = api_client.post(
        path=attach_path,
        data={
            'task_id': task_field.task_id,
        },
    )
    old = DelegationService.get_access_binding(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
    )
    with pytest.raises(PermissionDenied):
        DelegationService.create(
            token=grant.token,
            resource=mcp_settings.MCP_PUBLIC_URL,
            tool='get_upload_status',
            method='GET',
            path=status_path,
        )

    # assert
    assert created.status_code == 201, created.content
    assert completed.status_code == 200, completed.content
    assert exchanged.status_code == 200, exchanged.content
    assert polled.status_code == 200, polled.content
    assert attached.status_code == 200, attached.content
    assert str(poll_grant.delegation.connection_id) == (
        upload['connection_id']
    )
    assert str(attach_grant.delegation.connection_id) == (
        upload['connection_id']
    )
    assert Connection.objects.filter(user=grant.user).count() == 1
    assert old.access_token.scope == 'files:write'
