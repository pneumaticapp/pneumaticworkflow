import pytest

from src.ai.models import AIAgent, AIProvider
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


def test_retrieve__ok(api_client):

    """ Retrieve ok """

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
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert set(response.data.keys()) == {
        'id',
        'name',
        'base_url',
        'api_key_prefix',
        'vendor',
        'is_active',
        'usage',
    }
    assert response.data['id'] == provider.id
    assert response.data['name'] == provider.name
    assert response.data['base_url'] == provider.base_url
    assert response.data['is_active'] == provider.is_active
    assert response.data['usage'] == []
    assert 'api_key' not in response.data


def test_retrieve__usage__ok(api_client):

    """ Returns agents that use the provider """

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
    other_provider = AIProvider(
        account=account,
        name='Other',
        base_url='https://other.example.com',
        is_active=True,
    )
    other_provider.api_key = 'sk-or-v1-other'
    other_provider.save()
    agent_a = _create_agent(
        account=account,
        provider=provider,
        name='Agent A',
        email='agent-a@pneumatic.app',
    )
    agent_b = _create_agent(
        account=account,
        provider=provider,
        name='Agent B',
        email='agent-b@pneumatic.app',
    )
    _create_agent(
        account=account,
        provider=other_provider,
        name='Agent C',
        email='agent-c@pneumatic.app',
    )
    path = f'/ai/providers/{provider.id}'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data['usage'] == [
        {'id': agent_a.id, 'name': agent_a.name},
        {'id': agent_b.id, 'name': agent_b.name},
    ]


def test_retrieve__soft_deleted_agent__not_in_usage(api_client):

    """ Soft-deleted agents are excluded from usage """

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
    agent = _create_agent(
        account=account,
        provider=provider,
        name='Agent A',
        email='agent-a@pneumatic.app',
    )
    deleted_agent = _create_agent(
        account=account,
        provider=provider,
        name='Agent B',
        email='agent-b@pneumatic.app',
    )
    deleted_agent.delete()
    path = f'/ai/providers/{provider.id}'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data['usage'] == [
        {'id': agent.id, 'name': agent.name},
    ]


def test_retrieve__non_admin__ok(api_client):

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
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == provider.id
    assert 'api_key' not in response.data


def test_retrieve__unauthenticated__unauthorized(api_client):

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
    response = api_client.get(
        path=path,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_retrieve__not_found__not_found(api_client):

    """ Non-existent id """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    non_existent_id = 999999
    path = f'/ai/providers/{non_existent_id}'
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_retrieve__another_account__not_found(api_client):

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
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_retrieve__soft_deleted__not_found(api_client):

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
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message
