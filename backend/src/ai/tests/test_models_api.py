import pytest
from django.conf import settings
from django.core.cache import cache

from src.ai.models import AIProviderConnection
from src.processes.tests.fixtures import create_test_user

pytestmark = pytest.mark.django_db

MODELS = [
    {'slug': 'vendor/model-a', 'name': 'Alpha Model'},
    {'slug': 'vendor/model-b', 'name': 'Beta Model'},
]


@pytest.fixture(autouse=True)
def ai_performers_deployed(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )


@pytest.fixture(autouse=True)
def clear_cache():
    # the models cache is keyed by base URL and the locmem cache
    # survives between tests in one process
    cache.clear()
    yield
    cache.clear()


def _setup_user():
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    return user


def test_list__feature_on__models_returned(api_client, mocker):

    # arrange
    user = _setup_user()
    list_mock = mocker.patch(
        'src.ai.views.list_structured_output_models',
        return_value=MODELS,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/models')

    # assert
    assert response.status_code == 200
    assert response.data == MODELS
    list_mock.assert_called_once_with(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
    )


def test_list__connection_saved__uses_connection_creds(api_client, mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    AIProviderConnection.objects.create(
        account=user.account,
        name='OpenRouter',
        api_key='sk-or-v1-own-key',
    )
    list_mock = mocker.patch(
        'src.ai.views.list_structured_output_models',
        return_value=MODELS,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/models')

    # assert
    assert response.status_code == 200
    list_mock.assert_called_once_with(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-own-key',
    )


def test_list__second_request__served_from_cache(api_client, mocker):

    # arrange
    user = _setup_user()
    list_mock = mocker.patch(
        'src.ai.views.list_structured_output_models',
        return_value=MODELS,
    )
    api_client.token_authenticate(user)

    # act
    first = api_client.get('/ai/models')
    second = api_client.get('/ai/models')

    # assert
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.data == MODELS
    list_mock.assert_called_once()


def test_list__provider_unreachable__empty_not_cached(api_client, mocker):

    # arrange
    user = _setup_user()
    list_mock = mocker.patch(
        'src.ai.views.list_structured_output_models',
        return_value=None,
    )
    api_client.token_authenticate(user)

    # act
    first = api_client.get('/ai/models')
    second = api_client.get('/ai/models')

    # assert
    assert first.status_code == 200
    assert first.data == []
    assert second.data == []
    # a failure must not be cached: the next request retries
    assert list_mock.call_count == 2


def test_list__feature_off__forbidden(api_client, mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    list_mock = mocker.patch(
        'src.ai.views.list_structured_output_models',
        return_value=MODELS,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/models')

    # assert
    assert response.status_code == 403
    list_mock.assert_not_called()


def test_list__not_authenticated__unauthorized(api_client):

    # act
    response = api_client.get('/ai/models')

    # assert
    assert response.status_code == 401
