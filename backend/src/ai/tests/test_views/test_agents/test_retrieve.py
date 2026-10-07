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


def test_retrieve__by_owner__ok(api_client):

    """ Retrieve agent by id """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(
        account=account,
        provider=provider,
        photo='https://example.com/photo.jpg',
    )
    path = f'/ai/agents/{agent.id}'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == agent.id
    assert response.data['name'] == agent.name
    assert response.data['photo'] == agent.photo
    assert response.data['is_active'] == agent.is_active
    assert response.data['provider_id'] == provider.id
    assert response.data['model'] == agent.model
    assert response.data['system_prompt'] == agent.system_prompt


def test_retrieve__another_account__not_found(api_client):

    """ Retrieve agent from another account """

    # arrange
    account_1 = create_test_account()
    user = create_test_owner(account=account_1)
    account_2 = create_test_account(name='Another Company')
    agent = create_test_agent(account=account_2)
    path = f'/ai/agents/{agent.id}'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_retrieve__unauthenticated__unauthorized(api_client):

    """ Unauthenticated user """

    # arrange
    path = '/ai/agents/999999'
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_retrieve__guest__permission_denied(api_client):

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
    message = (
        'You do not have permission to perform this action.'
    )
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
