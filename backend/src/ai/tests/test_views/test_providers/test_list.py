import pytest

from src.ai.models import AIProvider
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

pytestmark = pytest.mark.django_db


def test_list__ok(api_client):

    """ List ok """

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
    path = '/ai/providers'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert set(response.data[0].keys()) == {
        'id',
        'name',
        'base_url',
        'api_key_prefix',
        'vendor',
        'is_active',
    }
    assert response.data[0]['id'] == provider.id
    assert response.data[0]['name'] == provider.name
    assert response.data[0]['base_url'] == provider.base_url
    assert response.data[0]['is_active'] == provider.is_active
    assert 'api_key' not in response.data[0]


def test_list__non_admin__ok(api_client):

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
    path = '/ai/providers'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == provider.id
    assert 'api_key' not in response.data[0]


def test_list__another_account__ok(api_client):

    """ Account filter """

    # arrange
    account_1 = create_test_account()
    user = create_test_owner(account=account_1)
    provider_1 = AIProvider(
        account=account_1,
        name='Provider 1',
        base_url='https://provider-1.example.com',
        is_active=True,
    )
    provider_1.api_key = 'sk-or-v1-example-1'
    provider_1.save()
    account_2 = create_test_account(name='Another Company')
    provider_2 = AIProvider(
        account=account_2,
        name='Provider 2',
        base_url='https://provider-2.example.com',
        is_active=True,
    )
    provider_2.api_key = 'sk-or-v1-example-2'
    provider_2.save()
    path = '/ai/providers'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == provider_1.id
    assert response.data[0]['id'] != provider_2.id
    assert 'api_key' not in response.data[0]


def test_list__soft_deleted__ok(api_client):

    """ Soft-deleted excluded """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider_1 = AIProvider(
        account=account,
        name='Active provider',
        base_url='https://active.example.com',
        is_active=True,
    )
    provider_1.api_key = 'sk-or-v1-example-1'
    provider_1.save()
    provider_2 = AIProvider(
        account=account,
        name='Deleted provider',
        base_url='https://deleted.example.com',
        is_active=True,
    )
    provider_2.api_key = 'sk-or-v1-example-2'
    provider_2.save()
    provider_2.delete()
    path = '/ai/providers'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == provider_1.id
    assert 'api_key' not in response.data[0]


def test_list__empty__ok(api_client):

    """ Empty list """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data == []


def test_list__pagination__ok(api_client):

    """ Pagination limit and offset """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider_1 = AIProvider(
        account=account,
        name='Provider 1',
        base_url='https://provider-1.example.com',
        is_active=True,
    )
    provider_1.api_key = 'sk-or-v1-example-1'
    provider_1.save()
    provider_2 = AIProvider(
        account=account,
        name='Provider 2',
        base_url='https://provider-2.example.com',
        is_active=True,
    )
    provider_2.api_key = 'sk-or-v1-example-2'
    provider_2.save()
    provider_3 = AIProvider(
        account=account,
        name='Provider 3',
        base_url='https://provider-3.example.com',
        is_active=True,
    )
    provider_3.api_key = 'sk-or-v1-example-3'
    provider_3.save()
    path = '/ai/providers?limit=2&offset=1'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path=path,
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == provider_2.id
    assert response.data['results'][1]['id'] == provider_3.id
    assert 'api_key' not in response.data['results'][0]


def test_list__unauthenticated__unauthorized(api_client):

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
    path = '/ai/providers'
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
    path = '/ai/providers'
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
