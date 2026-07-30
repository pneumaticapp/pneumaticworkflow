import pytest
from django.conf import settings

from src.ai.messages import MSG_AI_0002, MSG_AI_0003
from src.ai.models import AIProviderConnection
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db

DEFAULT_BASE_URL = 'https://openrouter.ai/api/v1'


@pytest.fixture(autouse=True)
def ai_performers_deployed(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )


@pytest.fixture(autouse=True)
def key_accepted(mocker):
    return mocker.patch(
        'src.ai.views.verify_api_key',
        return_value=True,
    )


def _setup_owner():

    # deliberately without ai_performers_enabled: the connection API
    # must work before the feature is on
    return create_test_user(is_account_owner=True)


def _create_connection(account, api_key='sk-or-v1-0123456789abcdef'):
    return AIProviderConnection.objects.create(
        account=account,
        name='OpenRouter',
        api_key=api_key,
    )


def test_get__no_connection__returns_null(api_client):

    # arrange
    user = _setup_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/connection')

    # assert
    assert response.status_code == 200
    assert response.data['connection'] is None


def test_get__with_connection__key_masked(api_client):

    # arrange
    user = _setup_owner()
    connection = _create_connection(
        user.account,
        api_key='sk-or-v1-0123456789abcdef',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/connection')

    # assert
    assert response.status_code == 200
    data = response.data['connection']
    assert data['id'] == connection.id
    assert data['base_url'] == DEFAULT_BASE_URL
    assert data['api_key_mask'] == 'sk-or-v1••••cdef'
    assert 'api_key' not in data


def test_put__creates_connection__feature_becomes_active(
    api_client,
    key_accepted,
):

    # arrange
    user = _setup_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/ai/connection',
        data={'api_key': 'sk-or-v1-0123456789abcdef'},
    )

    # assert
    assert response.status_code == 200
    connection = AIProviderConnection.objects.get(account=user.account)
    assert connection.api_key == 'sk-or-v1-0123456789abcdef'
    assert connection.base_url == DEFAULT_BASE_URL
    key_accepted.assert_called_once_with(
        base_url=DEFAULT_BASE_URL,
        api_key='sk-or-v1-0123456789abcdef',
    )
    # the saved key switches the feature on for the account
    agents_response = api_client.get('/ai/agents')
    assert agents_response.status_code == 200


def test_put__replaces_existing_connection(api_client):

    # arrange
    user = _setup_owner()
    stale = _create_connection(user.account, api_key='sk-or-old')
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/ai/connection',
        data={'api_key': 'sk-or-v1-0123456789abcdef'},
    )

    # assert
    assert response.status_code == 200
    connections = AIProviderConnection.objects.filter(account=user.account)
    assert connections.count() == 1
    assert connections.get().api_key == 'sk-or-v1-0123456789abcdef'
    stale.refresh_from_db()
    assert stale.is_deleted is True


def test_put__custom_base_url__saved_and_verified(
    api_client,
    key_accepted,
):

    # arrange
    user = _setup_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/ai/connection',
        data={
            'api_key': 'custom-key-0123456789',
            'base_url': 'https://llm.example.com/v1',
        },
    )

    # assert
    assert response.status_code == 200
    connection = AIProviderConnection.objects.get(account=user.account)
    assert connection.base_url == 'https://llm.example.com/v1'
    key_accepted.assert_called_once_with(
        base_url='https://llm.example.com/v1',
        api_key='custom-key-0123456789',
    )


def test_put__rejected_key__validation_error(api_client, key_accepted):

    # arrange
    key_accepted.return_value = False
    user = _setup_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/ai/connection',
        data={'api_key': 'sk-or-v1-wrong'},
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_AI_0003
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert not AIProviderConnection.objects.filter(
        account=user.account,
    ).exists()


def test_put__provider_unreachable__saves_anyway(api_client, key_accepted):

    # arrange
    key_accepted.return_value = None
    user = _setup_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/ai/connection',
        data={'api_key': 'sk-or-v1-0123456789abcdef'},
    )

    # assert
    assert response.status_code == 200
    assert AIProviderConnection.objects.filter(
        account=user.account,
    ).exists()


def test_delete__removes_connection__feature_off(api_client):

    # arrange
    user = _setup_owner()
    _create_connection(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.delete('/ai/connection')

    # assert
    assert response.status_code == 200
    assert response.data['connection'] is None
    assert not AIProviderConnection.objects.filter(
        account=user.account,
    ).exists()
    agents_response = api_client.get('/ai/agents')
    assert agents_response.status_code == 403


def test_get__not_admin__permission_denied(api_client):

    # arrange
    user = _setup_owner()
    not_admin = create_test_not_admin(account=user.account)
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.get('/ai/connection')

    # assert
    assert response.status_code == 403


def test_get__feature_not_deployed__permission_denied(api_client, mocker):

    # arrange
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': False},
    )
    user = _setup_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/connection')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_AI_0002
