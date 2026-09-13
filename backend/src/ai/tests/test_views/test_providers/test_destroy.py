import pytest

from src.ai.exceptions import AIServiceException
from src.ai.messages import MSG_AI_0005
from src.ai.models import AIAgent, AIProvider
from src.ai.services.provider import AIProviderService
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def _create_agent(account, provider, name, email):
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name=name,
        is_ai=True,
    )
    return AIAgent.objects.create(
        account=account,
        name=name,
        model='openai/gpt-4o',
        system_prompt='You are helpful.',
        is_active=True,
        provider=provider,
        user=agent_user,
    )


def test_destroy__ok(api_client, mocker):

    """ Delete ok """

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
    path = f'/ai/providers/{provider.id}'
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    delete_mock = mocker.patch(
        'src.ai.views.AIProviderService.delete',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 204
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    delete_mock.assert_called_once_with()


def test_destroy__used_by_agent__validation_error(api_client):

    """ Provider used by an agent """

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
    _create_agent(
        account=account,
        provider=provider,
        name='Research assistant',
        email='agent@pneumatic.app',
    )
    path = f'/ai/providers/{provider.id}'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(MSG_AI_0005)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert AIProvider.objects.filter(id=provider.id).exists()


def test_destroy__unauthenticated__unauthorized(api_client):

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
    path = f'/ai/providers/{provider.id}'
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_destroy__guest__permission_denied(api_client):

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
    path = f'/ai/providers/{provider.id}'
    message = 'You do not have permission to perform this action.'
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.delete(
        path=path,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_destroy__non_admin__permission_denied(api_client):

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
    path = f'/ai/providers/{provider.id}'
    message = 'You do not have permission to perform this action.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_destroy__not_found__not_found(api_client):

    """ Non-existent id """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    non_existent_id = 999999
    path = f'/ai/providers/{non_existent_id}'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_destroy__another_account__not_found(api_client):

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
    path = f'/ai/providers/{provider.id}'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_destroy__soft_deleted__not_found(api_client):

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
    path = f'/ai/providers/{provider.id}'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_destroy__service_exception__validation_error(api_client, mocker):

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
    path = f'/ai/providers/{provider.id}'
    error_message = 'AI service error'
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    delete_mock = mocker.patch(
        'src.ai.views.AIProviderService.delete',
        side_effect=AIServiceException(message=error_message),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
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
    delete_mock.assert_called_once_with()
