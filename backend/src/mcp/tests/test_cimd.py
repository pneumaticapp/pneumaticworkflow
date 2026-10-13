import base64
import hashlib

import pytest
from oauth2_provider.models import Application
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from src.generics.tests.clients import PneumaticApiClient
from src.mcp.models import ClientPolicy

pytestmark = pytest.mark.django_db


def test_cimd__https_metadata_client__registered_without_introspection(
    api_client: PneumaticApiClient,
    mocker: MockerFixture,
    mcp_settings: SettingsWrapper,
):
    # arrange
    client_id = 'https://client.test/metadata.json'
    fetch_mock = mocker.patch(
        target='oauth2_provider.cimd.SafeMetadataFetcher.fetch',
        return_value=(
            {
                'client_id': client_id,
                'client_name': 'Metadata client',
                'redirect_uris': ['https://client.test/callback'],
                'grant_types': ['authorization_code', 'refresh_token'],
                'response_types': ['code'],
                'token_endpoint_auth_method': 'none',
            },
            3600,
        ),
    )
    challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(b'v' * 64).digest(),
        )
        .decode()
        .rstrip('=')
    )

    # act
    response = api_client.get(
        path='/oauth/mcp/authorize',
        data={
            'client_id': client_id,
            'redirect_uri': 'https://client.test/callback',
            'response_type': 'code',
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
    )
    app = Application.objects.get(client_id=client_id)
    policy = ClientPolicy.objects.get(application=app)

    # assert
    assert response.status_code == 302, response.content
    assert app.registration_source == 'cimd'
    assert policy.can_introspect is False
    fetch_mock.assert_called_once_with(client_id)


def test_cimd__private_metadata_url__deny(
    api_client: PneumaticApiClient,
    mcp_settings: SettingsWrapper,
):
    # arrange
    client_id = 'https://127.0.0.1/private.json'

    # act
    response = api_client.get(
        path='/oauth/mcp/authorize',
        data={
            'client_id': client_id,
            'redirect_uri': 'https://client.test/callback',
            'response_type': 'code',
            'code_challenge': 'v' * 43,
            'code_challenge_method': 'S256',
            'resource': mcp_settings.MCP_PUBLIC_URL,
        },
    )

    # assert
    assert response.status_code == 400
    assert not Application.objects.filter(client_id=client_id).exists()
