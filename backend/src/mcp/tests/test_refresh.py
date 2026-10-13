import secrets
from types import SimpleNamespace

import pytest
from oauth2_provider.models import RefreshToken
from pytest_django.fixtures import SettingsWrapper

from src.authentication.services.delegation import DelegationService
from src.generics.tests.clients import PneumaticApiClient
from src.authentication.exceptions import (
    InvalidMcpToken,
)
from src.mcp.models import ClientPolicy, RefreshBinding

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('reused,status', [(False, 200), (True, 400)])
def test_refresh__rotation_or_reuse__expected_connection_state(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    reused: bool,
    status: int,
):
    # arrange
    token = secrets.token_urlsafe(32)
    refresh = RefreshToken.objects.create(
        token=token,
        application=grant.app,
        user=grant.user,
        access_token=grant.access,
    )
    RefreshBinding.objects.create(
        refresh_token=refresh,
        connection=grant.connection,
    )
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': token,
        'client_id': grant.app.client_id,
        'resource': mcp_settings.MCP_PUBLIC_URL,
    }

    if reused:
        issued = api_client.post(
            path='/oauth/mcp/token',
            data=data,
            format='multipart',
        ).json()

    # act
    response = api_client.post(
        path='/oauth/mcp/token',
        data=data,
        format='multipart',
    )
    token_to_check = (
        issued['access_token']
        if reused
        else response.json()['access_token']
    )
    grant.connection.refresh_from_db()

    # assert
    assert response.status_code == status
    if reused:
        assert response.json()['error'] == 'invalid_grant'
        with pytest.raises(InvalidMcpToken):
            DelegationService.get_access_binding(
                token=token_to_check,
                resource=mcp_settings.MCP_PUBLIC_URL,
            )
        assert grant.connection.revoked_at is not None
    else:
        binding = DelegationService.get_access_binding(
            token=token_to_check,
            resource=mcp_settings.MCP_PUBLIC_URL,
        )
        assert response.json()['refresh_token'] != token
        assert response.json()['expires_in'] == 900
        assert binding.connection_id == grant.connection.pk
        assert grant.connection.revoked_at is None


def test_refresh__disabled_client__deny(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    token = secrets.token_urlsafe(32)
    refresh = RefreshToken.objects.create(
        token=token,
        application=grant.app,
        user=grant.user,
        access_token=grant.access,
    )
    RefreshBinding.objects.create(
        refresh_token=refresh,
        connection=grant.connection,
    )
    ClientPolicy.objects.filter(application=grant.app).update(is_active=False)

    # act
    response = api_client.post(
        path='/oauth/mcp/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': token,
            'client_id': grant.app.client_id,
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
        format='multipart',
    )

    # assert
    assert response.status_code in {400, 401}
    assert response.json()['error'] in {'invalid_client', 'invalid_grant'}
