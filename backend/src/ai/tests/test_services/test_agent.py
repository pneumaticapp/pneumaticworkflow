import string

from typing import Optional

import pytest

from src.ai.exceptions import AIAgentNameNotUniqueException
from src.ai.messages import MSG_AI_0004
from src.ai.models import AIAgent, AIProvider
from src.ai.services.agent import AIAgentService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def _create_provider(account) -> AIProvider:
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    return provider


def _create_agent(
    account,
    name: str = 'Research assistant',
    photo: Optional[str] = None,
    email: str = 'agent@pneumatic.app',
    system_prompt: str = 'You are helpful.',
) -> AIAgent:
    provider = _create_provider(account)
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name=name,
        photo=photo,
        is_ai=True,
    )
    return AIAgent.objects.create(
        account=account,
        name=name,
        model='openai/gpt-4o',
        system_prompt=system_prompt,
        is_active=True,
        photo=photo,
        provider=provider,
        user=agent_user,
    )


def test_get_agent_email__owner_domain_and_random_local__ok(mocker):

    """ Domain from owner email, local from random chars """

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        email='boss@company.io',
    )
    random_local = 'x7k2m9qp4abcdefghijk'
    get_random_string_mock = mocker.patch(
        'src.ai.services.agent.get_random_string',
        return_value=random_local,
    )
    service = AIAgentService(user=owner)

    # act
    email = service._get_agent_email()

    # assert
    assert email == f'ai-agent-{random_local}@company.io'
    get_random_string_mock.assert_called_once_with(
        length=20,
        allowed_chars=string.ascii_letters + string.digits,
    )


def test_get_agent_email__already_exists__regenerate(mocker):

    """ Occupied generated email is regenerated """

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        email='boss@company.io',
    )
    create_test_admin(
        account=account,
        email='ai-agent-aaaaaaaaaaaaaaaaaaaa@company.io',
    )
    mocker.patch(
        'src.ai.services.agent.get_random_string',
        side_effect=['aaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbbb'],
    )
    service = AIAgentService(user=owner)

    # act
    email = service._get_agent_email()

    # assert
    assert email == 'ai-agent-bbbbbbbbbbbbbbbbbbbb@company.io'


def test_create_instance__ok(mocker):

    """ Agent and backing user created from serializer data """

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        email='boss@company.io',
    )
    provider = _create_provider(account)
    name = 'Research assistant'
    model = 'openai/gpt-4o'
    system_prompt = 'You are a helpful research assistant.'
    photo = 'https://example.com/images/assistant.jpg'
    random_local = 'x7k2m9qp4abc'
    mocker.patch(
        'src.ai.services.agent.get_random_string',
        return_value=random_local,
    )
    mocker.patch(
        'src.accounts.services.user.UserService._create_actions',
    )
    service = AIAgentService(user=owner)

    # act
    agent = service._create_instance(
        name=name,
        model=model,
        is_active=True,
        system_prompt=system_prompt,
        photo=photo,
        provider_id=provider.id,
    )

    # assert
    assert agent == service.instance
    assert agent.account == account
    assert agent.name == name
    assert agent.model == model
    assert agent.is_active is True
    assert agent.system_prompt == system_prompt
    assert agent.photo == photo
    assert agent.provider_id == provider.id
    assert agent.user_id is not None

    agent_user = agent.user
    assert agent_user.account == account
    assert agent_user.email == f'ai-agent-{random_local}@company.io'
    assert agent_user.first_name == name
    assert agent_user.last_name == ''
    assert agent_user.photo == photo
    assert agent_user.is_admin is True
    assert agent_user.is_ai is True
    assert agent_user.is_account_owner is False
    assert agent_user.password
    assert agent_user.is_tasks_digest_subscriber is False
    assert agent_user.is_digest_subscriber is False
    assert agent_user.is_newsletters_subscriber is False
    assert agent_user.is_special_offers_subscriber is False
    assert agent_user.is_new_tasks_subscriber is False
    assert agent_user.is_complete_tasks_subscriber is False
    assert agent_user.is_comments_mentions_subscriber is False


def test_create_instance__user_service_kwargs__ok(mocker):

    """ UserService.create called without password """

    # arrange
    account = create_test_account()
    owner = create_test_owner(
        account=account,
        email='boss@company.io',
    )
    provider = _create_provider(account)
    name = 'Research assistant'
    model = 'openai/gpt-4o'
    photo = 'https://example.com/images/assistant.jpg'
    random_local = 'x7k2m9qp4abc'
    mocker.patch(
        'src.ai.services.agent.get_random_string',
        return_value=random_local,
    )
    agent_user = create_test_admin(
        account=account,
        email='agent-user@pneumatic.app',
        first_name=name,
        is_ai=True,
    )
    create_user_mock = mocker.patch(
        'src.ai.services.agent.UserService.create',
        return_value=agent_user,
    )
    service = AIAgentService(user=owner)

    # act
    service._create_instance(
        name=name,
        model=model,
        system_prompt='You are a helpful research assistant.',
        photo=photo,
        provider_id=provider.id,
    )

    # assert
    create_user_mock.assert_called_once_with(
        account=account,
        email=f'ai-agent-{random_local}@company.io',
        first_name=name,
        photo=photo,
        is_admin=True,
        is_ai=True,
        is_tasks_digest_subscriber=False,
        is_digest_subscriber=False,
        is_newsletters_subscriber=False,
        is_special_offers_subscriber=False,
        is_new_tasks_subscriber=False,
        is_complete_tasks_subscriber=False,
        is_comments_mentions_subscriber=False,
    )


def test_create_instance__defaults__ok(mocker):

    """ Optional fields use defaults """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = _create_provider(account)
    mocker.patch(
        'src.accounts.services.user.UserService._create_actions',
    )
    service = AIAgentService(user=owner)

    # act
    agent = service._create_instance(
        name='Research assistant',
        model='openai/gpt-4o',
        system_prompt='You are helpful.',
        provider_id=provider.id,
    )

    # assert
    assert agent.is_active is True
    assert agent.system_prompt == 'You are helpful.'
    assert agent.photo is None
    assert agent.user.photo is None
    assert agent.user.email.endswith('@pneumatic.app')


def test_create_instance__duplicate_name__raise_exception(mocker):

    """ Duplicate agent name on the same account """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = _create_provider(account)
    name = 'Research assistant'
    mocker.patch(
        'src.accounts.services.user.UserService._create_actions',
    )
    service = AIAgentService(user=owner)
    service._create_instance(
        name=name,
        model='openai/gpt-4o',
        system_prompt='You are helpful.',
        provider_id=provider.id,
    )

    # act
    with pytest.raises(AIAgentNameNotUniqueException) as ex:
        service._create_instance(
            name=name,
            model='openai/gpt-4o',
            system_prompt='You are helpful.',
            provider_id=provider.id,
        )

    # assert
    assert str(ex.value.message) == str(MSG_AI_0004)
    assert AIAgent.objects.filter(account=account, name=name).count() == 1


def test_partial_update__name__updates_user(mocker):

    """ Agent name change is copied to the related user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = _create_agent(
        account=account,
        name='Research assistant',
    )
    new_name = 'Support assistant'
    mocker.patch(
        'src.accounts.services.user.send_user_updated_notification',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(name=new_name)

    # assert
    agent.user.refresh_from_db()
    assert result.name == new_name
    assert agent.user.first_name == new_name
    assert agent.user.photo is None


def test_partial_update__photo__updates_user(mocker):

    """ Agent photo change is copied to the related user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_photo = 'https://example.com/images/old.jpg'
    agent = _create_agent(
        account=account,
        photo=old_photo,
    )
    new_photo = 'https://example.com/images/new.jpg'
    mocker.patch(
        'src.accounts.services.user.send_user_updated_notification',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(photo=new_photo)

    # assert
    agent.user.refresh_from_db()
    assert result.photo == new_photo
    assert agent.user.photo == new_photo
    assert agent.user.first_name == agent.name


def test_partial_update__name_and_photo__updates_user(mocker):

    """ Agent name and photo changes are copied to the related user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    agent = _create_agent(
        account=account,
        name='Research assistant',
        photo='https://example.com/images/old.jpg',
    )
    new_name = 'Support assistant'
    new_photo = 'https://example.com/images/new.jpg'
    mocker.patch(
        'src.accounts.services.user.send_user_updated_notification',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(name=new_name, photo=new_photo)

    # assert
    agent.user.refresh_from_db()
    assert result.name == new_name
    assert result.photo == new_photo
    assert agent.user.first_name == new_name
    assert agent.user.photo == new_photo


def test_partial_update__other_fields__user_not_updated(mocker):

    """ Fields other than name and photo do not update the user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    name = 'Research assistant'
    photo = 'https://example.com/images/old.jpg'
    agent = _create_agent(
        account=account,
        name=name,
        photo=photo,
    )
    user_partial_update_mock = mocker.patch(
        'src.ai.services.agent.UserService.partial_update',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    result = service.partial_update(
        is_active=False,
        model='openai/gpt-4o-mini',
        system_prompt='New prompt',
    )

    # assert
    agent.user.refresh_from_db()
    assert result.is_active is False
    assert result.model == 'openai/gpt-4o-mini'
    assert result.system_prompt == 'New prompt'
    assert result.name == name
    assert result.photo == photo
    assert agent.user.first_name == name
    assert agent.user.photo == photo
    user_partial_update_mock.assert_not_called()


def test_partial_update__duplicate_name__raise_exception(mocker):

    """ Duplicate agent name on the same account """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    existent_name = 'Research assistant'
    _create_agent(
        account=account,
        name=existent_name,
        email='agent-one@pneumatic.app',
    )
    agent = _create_agent(
        account=account,
        name='Support assistant',
        email='agent-two@pneumatic.app',
    )
    service = AIAgentService(user=owner, instance=agent)

    # act
    with pytest.raises(AIAgentNameNotUniqueException) as ex:
        service.partial_update(name=existent_name)

    # assert
    assert str(ex.value.message) == str(MSG_AI_0004)
    agent.refresh_from_db()
    agent.user.refresh_from_db()
    assert agent.name == 'Support assistant'
    assert agent.user.first_name == 'Support assistant'
