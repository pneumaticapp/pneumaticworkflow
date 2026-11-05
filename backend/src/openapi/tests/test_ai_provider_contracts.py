"""Provider contracts through real validation, storage and vendor handlers."""

import json
import socket

import pytest
from requests import Response

from src.ai.enums import AIVendor
from src.ai.models import AIProvider
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


@pytest.fixture
def provider_transport(mocker):
    mocker.patch(
        'src.ai.serializers.socket.getaddrinfo',
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '',
                       ('8.8.8.8', 0))],
    )

    def vendor_response(method, **kwargs):
        payload = (
            {'data': [{'id': 'contract-model', 'object': 'model'}]}
            if method == 'GET' else
            {'choices': [{'message': {'content': 'Hello world'}}]}
        )
        response = Response()
        response.status_code = 200
        response._content = json.dumps(payload).encode('utf-8')
        response.headers['Content-Type'] = 'application/json'
        return response

    return mocker.patch('requests.request', side_effect=vendor_response)


@pytest.mark.parametrize('by_vendor', [False, True])
def test_provider__real_create_retrieve_update__matches_contract(
    contract_api_client, provider_transport, by_vendor,
) -> None:
    # arrange
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)
    secret = 'local-contract-provider-key'
    path = '/ai/providers/by-vendor' if by_vendor else '/ai/providers'
    data = (
        {'vendor': AIVendor.OPENAI, 'api_key': secret}
        if by_vendor else {
            'name': 'Contract provider',
            'base_url': 'https://provider.example.test/v1', 'api_key': secret,
        }
    )

    # act
    created = contract_api_client.post(path, data=data, format='json')

    # assert
    assert created.status_code == 201
    provider = AIProvider.objects.get(id=created.json()['id'])
    expected_vendor = AIVendor.OPENAI if by_vendor else AIVendor.CUSTOM
    assert provider.vendor == created.json()['vendor'] == expected_vendor
    assert provider.api_key == secret
    assert provider.api_key_encrypted != secret
    assert 'api_key' not in created.json()
    assert provider_transport.call_count == 2

    retrieved = contract_api_client.get(f'/ai/providers/{provider.id}')
    assert retrieved.status_code == 200
    assert retrieved.json() == created.json()

    updated = contract_api_client.patch(
        f'/ai/providers/{provider.id}',
        data={'name': 'Renamed provider', 'api_key': 'rotated-contract-key'},
        format='json',
    )
    assert updated.status_code == 200
    assert updated.json()['name'] == 'Renamed provider'
    assert 'api_key' not in updated.json()
    provider.refresh_from_db()
    assert provider.name == 'Renamed provider'
    assert provider.api_key == 'rotated-contract-key'


@pytest.mark.parametrize('path', ['/ai/providers', '/ai/providers/by-vendor'])
def test_provider__missing_fields__error_contract(
    contract_api_client, path,
) -> None:
    owner = create_test_owner()
    contract_api_client.token_authenticate(owner)

    response = contract_api_client.post(path, data={}, format='json')

    assert response.status_code == 400
    assert not AIProvider.objects.filter(account=owner.account).exists()


@pytest.mark.parametrize('method', ['get', 'patch'])
def test_provider__missing_id__error_contract(
    contract_api_client, method,
) -> None:
    contract_api_client.token_authenticate(create_test_owner())

    response = getattr(contract_api_client, method)(
        '/ai/providers/2147483647', data={}, format='json',
    )

    assert response.status_code == 404
