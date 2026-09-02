import pytest

from src.ai.exceptions import AIServiceException
from src.ai.models import AIProvider
from src.ai.services.provider import AIProviderService
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_models__ok(api_client, mocker):

    """ List models ok """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}/models'
    models = [
        {
            'name': 'GPT-4o',
            'slug': 'openai/gpt-4o',
        },
        {
            'name': 'Claude Sonnet',
            'slug': 'anthropic/claude-sonnet-4',
        },
    ]
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    get_models_mock = mocker.patch(
        'src.ai.views.AIProviderService.get_models',
        return_value=models,
        create=True,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert set(response.data[0].keys()) == {'name', 'slug'}
    assert response.data[0]['name'] == 'GPT-4o'
    assert response.data[0]['slug'] == 'openai/gpt-4o'
    assert response.data[1]['name'] == 'Claude Sonnet'
    assert response.data[1]['slug'] == 'anthropic/claude-sonnet-4'
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_models_mock.assert_called_once_with()


def test_models__non_admin__ok(api_client, mocker):

    """ Non-admin user """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}/models'
    models = [
        {
            'name': 'GPT-4o',
            'slug': 'openai/gpt-4o',
        },
    ]
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    get_models_mock = mocker.patch(
        'src.ai.views.AIProviderService.get_models',
        return_value=models,
        create=True,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['name'] == 'GPT-4o'
    assert response.data[0]['slug'] == 'openai/gpt-4o'
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_models_mock.assert_called_once_with()


def test_models__unauthenticated__unauthorized(api_client):

    """ Unauthenticated """

    # arrange
    account = create_test_account()
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}/models'
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_models__guest__permission_denied(api_client):

    """ Guest user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    path = f'/ai/providers/{provider.id}/models'
    message = 'You do not have permission to perform this action.'
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.get(
        path=path,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_models__not_found__not_found(api_client):

    """ Non-existent id """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    non_existent_id = 999999
    path = f'/ai/providers/{non_existent_id}/models'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_models__another_account__not_found(api_client):

    """ Another account """

    # arrange
    account_1 = create_test_account()
    user = create_test_owner(account=account_1)
    account_2 = create_test_account(name='Another Company')
    provider = AIProvider(
        account=account_2,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}/models'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_models__soft_deleted__not_found(api_client):

    """ Soft-deleted provider """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    provider.delete()
    path = f'/ai/providers/{provider.id}/models'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_models__service_exception__validation_error(api_client, mocker):

    """ Service exception """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}/models'
    error_message = 'AI service error'
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    get_models_mock = mocker.patch(
        'src.ai.views.AIProviderService.get_models',
        side_effect=AIServiceException(message=error_message),
        create=True,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    get_models_mock.assert_called_once_with()
