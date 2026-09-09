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


def test_partial_update__name__ok(api_client, mocker):

    """ Update agent name """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(
        account=account,
        provider=provider,
    )
    updated_agent = create_test_agent(
        account=account,
        provider=provider,
        name='Updated name',
    )
    path = f'/ai/agents/{agent.id}'
    data = {
        'name': 'Updated name',
    }
    ai_agent_service_init_mock = mocker.patch.object(
        AIAgentService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIAgentService.partial_update',
        return_value=updated_agent,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == updated_agent.id
    assert response.data['name'] == 'Updated name'
    ai_agent_service_init_mock.assert_called_once_with(
        user=user,
        instance=agent,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name='Updated name',
    )


def test_partial_update__service_exc__validation_error(
    api_client,
    mocker,
):

    """ Update agent — service exception """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(
        account=account,
        provider=provider,
    )
    path = f'/ai/agents/{agent.id}'
    data = {
        'name': 'Updated name',
    }
    error_message = 'AI service error'
    ai_agent_service_init_mock = mocker.patch.object(
        AIAgentService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIAgentService.partial_update',
        side_effect=AIServiceException(
            message=error_message,
        ),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    ai_agent_service_init_mock.assert_called_once_with(
        user=user,
        instance=agent,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name='Updated name',
    )


def test_partial_update__unauthenticated__unauthorized(
    api_client,
):

    """ Unauthenticated user """

    # arrange
    path = '/ai/agents/999999'
    data = {
        'name': 'Updated name',
    }
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_partial_update__not_admin__permission_denied(
    api_client,
):

    """ Not admin user """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    agent = create_test_agent(account=account)
    path = f'/ai/agents/{agent.id}'
    data = {
        'name': 'Updated name',
    }
    message = (
        'You do not have permission to perform this action.'
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_partial_update__not_found__not_found(api_client):

    """ Agent not found """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    non_existent_id = 999999
    path = f'/ai/agents/{non_existent_id}'
    data = {
        'name': 'Updated name',
    }
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_partial_update__guest__permission_denied(api_client):

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
    path = '/ai/agents/999999'
    data = {
        'name': 'Updated name',
    }
    message = (
        'You do not have permission to perform this action.'
    )
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.patch(
        path=path,
        data=data,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message
