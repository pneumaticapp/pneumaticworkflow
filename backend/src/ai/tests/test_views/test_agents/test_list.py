import pytest

from src.ai.tests.fixtures import (
    create_test_agent,
    create_test_provider,
)
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_list__by_owner__ok(api_client):

    """ List agents for account owner """

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
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == agent.id
    assert response.data[0]['name'] == agent.name
    assert response.data[0]['photo'] == agent.photo
    assert response.data[0]['is_active'] == agent.is_active
    assert response.data[0]['provider_id'] == provider.id
    assert response.data[0]['model'] == agent.model
    assert response.data[0]['system_prompt'] == agent.system_prompt


def test_list__pagination__ok(api_client):

    """ List agents with pagination """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    create_test_agent(
        account=account,
        provider=provider,
        name='Agent 1',
    )
    agent_2 = create_test_agent(
        account=account,
        provider=provider,
        name='Agent 2',
    )
    agent_3 = create_test_agent(
        account=account,
        provider=provider,
        name='Agent 3',
    )
    path = '/ai/agents?limit=2&offset=1'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == agent_2.id
    assert response.data['results'][1]['id'] == agent_3.id


def test_list__another_account__not_returned(api_client):

    """ List agents returns only own account """

    # arrange
    account_1 = create_test_account()
    user = create_test_owner(account=account_1)
    agent_1 = create_test_agent(
        account=account_1,
        name='Agent 1',
    )
    account_2 = create_test_account(name='Another Company')
    create_test_agent(
        account=account_2,
        name='Agent 2',
    )
    path = '/ai/agents'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == agent_1.id


def test_list__unauthenticated__unauthorized(api_client):

    """ Unauthenticated user """

    # arrange
    path = '/ai/agents'
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_list__guest__permission_denied(api_client):

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
