import pytest
from django.conf import settings

from src.ai.messages import MSG_AI_0001, MSG_AI_0002
from src.ai.models import AIAgent
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_user,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def ai_performers_enabled(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )


def _setup_user():
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    return user


def _create_agent(account, name='Analyst'):
    return AIAgent.objects.create(
        account=account,
        name=name,
        model_slug='test/model',
    )


def test_list__ok(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    foreign_account = create_test_account()
    _create_agent(foreign_account, name='Foreign')
    deleted_agent = _create_agent(user.account, name='Deleted')
    deleted_agent.delete()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/agents')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == agent.id
    assert response.data[0]['name'] == agent.name
    assert response.data[0]['model_slug'] == agent.model_slug


def test_list__feature_disabled__permission_denied(api_client):

    # arrange
    user = create_test_user(is_account_owner=True)
    _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/ai/agents')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_AI_0002


def test_retrieve__ok(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/ai/agents/{agent.id}')

    # assert
    assert response.status_code == 200
    assert response.data['id'] == agent.id
    assert response.data['name'] == agent.name


def test_retrieve__foreign_account__not_found(api_client):

    # arrange
    user = _setup_user()
    foreign_account = create_test_account()
    agent = _create_agent(foreign_account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/ai/agents/{agent.id}')

    # assert
    assert response.status_code == 404


def test_create__ok(api_client):

    # arrange
    user = _setup_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/ai/agents',
        data={
            'name': 'Analyst',
            'model_slug': 'anthropic/claude-3',
            'system_prompt': 'You review contracts.',
            'temperature': 0.5,
        },
    )

    # assert
    assert response.status_code == 201
    agent = AIAgent.objects.get(id=response.data['id'])
    assert agent.account_id == user.account_id
    assert agent.name == 'Analyst'
    assert agent.model_slug == 'anthropic/claude-3'
    assert agent.system_prompt == 'You review contracts.'
    assert agent.temperature == 0.5
    assert agent.is_active is True


def test_create__duplicate_name__validation_error(api_client):

    # arrange
    user = _setup_user()
    _create_agent(user.account, name='Analyst')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/ai/agents',
        data={
            'name': 'Analyst',
            'model_slug': 'test/model',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == MSG_AI_0001
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_create__not_admin__permission_denied(api_client):

    # arrange
    user = _setup_user()
    not_admin = create_test_not_admin(account=user.account)
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(
        '/ai/agents',
        data={
            'name': 'Analyst',
            'model_slug': 'test/model',
        },
    )

    # assert
    assert response.status_code == 403


def test_partial_update__ok(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.patch(
        f'/ai/agents/{agent.id}',
        data={
            'name': 'Reviewer',
            'is_active': False,
        },
    )

    # assert
    assert response.status_code == 200
    agent.refresh_from_db()
    assert agent.name == 'Reviewer'
    assert agent.is_active is False


def test_destroy__ok(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/ai/agents/{agent.id}')

    # assert
    assert response.status_code == 204
    assert not AIAgent.objects.filter(id=agent.id).exists()
