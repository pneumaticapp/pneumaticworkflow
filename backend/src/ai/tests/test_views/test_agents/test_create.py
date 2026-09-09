import pytest

from src.ai.exceptions import AIServiceException
from src.ai.services.agent import AIAgentService
from src.ai.tests.fixtures import (
    create_test_agent,
    create_test_provider,
)
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


def test_create__all_fields__ok(api_client, mocker):

    """ Create agent with all fields """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(
        account=account,
        provider=provider,
        photo='https://example.com/photo.jpg',
    )
    path = '/ai/agents'
    data = {
        'name': 'Research assistant',
        'photo': 'https://example.com/photo.jpg',
        'is_active': True,
        'provider_id': provider.id,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are helpful.',
    }
    ai_agent_service_init_mock = mocker.patch.object(
        AIAgentService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIAgentService.create',
        return_value=agent,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['id'] == agent.id
    assert response.data['name'] == 'Research assistant'
    assert response.data['photo'] == 'https://example.com/photo.jpg'
    assert response.data['is_active'] is True
    assert response.data['provider_id'] == provider.id
    assert response.data['model'] == 'openai/gpt-4o'
    assert response.data['system_prompt'] == 'You are helpful.'
    ai_agent_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='Research assistant',
        photo='https://example.com/photo.jpg',
        is_active=True,
        provider_id=provider.id,
        model='openai/gpt-4o',
        system_prompt='You are helpful.',
    )


def test_create__minimal_fields__ok(api_client, mocker):

    """ Create agent with minimal fields """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(
        account=account,
        provider=provider,
    )
    path = '/ai/agents'
    data = {
        'name': 'Research assistant',
        'is_active': True,
        'provider_id': provider.id,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are helpful.',
    }
    ai_agent_service_init_mock = mocker.patch.object(
        AIAgentService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIAgentService.create',
        return_value=agent,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['id'] == agent.id
    assert response.data['name'] == 'Research assistant'
    assert response.data['photo'] is None
    ai_agent_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='Research assistant',
        is_active=True,
        provider_id=provider.id,
        model='openai/gpt-4o',
        system_prompt='You are helpful.',
    )


def test_create__service_exception__validation_error(
    api_client,
    mocker,
):

    """ Create agent — service exception """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    path = '/ai/agents'
    data = {
        'name': 'Research assistant',
        'is_active': True,
        'provider_id': provider.id,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are helpful.',
    }
    error_message = 'AI service error'
    ai_agent_service_init_mock = mocker.patch.object(
        AIAgentService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIAgentService.create',
        side_effect=AIServiceException(
            message=error_message,
        ),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    ai_agent_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='Research assistant',
        is_active=True,
        provider_id=provider.id,
        model='openai/gpt-4o',
        system_prompt='You are helpful.',
    )


def test_create__unauthenticated__unauthorized(api_client):

    """ Unauthenticated user """

    # arrange
    path = '/ai/agents'
    data = {
        'name': 'Research assistant',
        'is_active': True,
        'provider_id': 1,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are helpful.',
    }
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_create__not_admin__permission_denied(api_client):

    """ Not admin user """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    path = '/ai/agents'
    data = {
        'name': 'Research assistant',
        'is_active': True,
        'provider_id': 1,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are helpful.',
    }
    message = (
        'You do not have permission to perform this action.'
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_create__guest__permission_denied(api_client):

    """ Guest user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
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
    path = '/ai/agents'
    data = {
        'name': 'Research assistant',
        'is_active': True,
        'provider_id': 1,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are helpful.',
    }
    message = (
        'You do not have permission to perform this action.'
    )
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.post(
        path=path,
        data=data,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message
