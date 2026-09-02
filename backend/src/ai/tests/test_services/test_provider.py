from typing import Optional

import pytest

from src.ai.exceptions import AIProviderInUseException
from src.ai.messages import MSG_AI_0005
from src.ai.models import AIAgent, AIProvider
from src.ai.services.provider import AIProviderService
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
    provider,
    name: str = 'Research assistant',
    email: str = 'agent@pneumatic.app',
    photo: Optional[str] = None,
) -> AIAgent:
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
        system_prompt='You are helpful.',
        is_active=True,
        photo=photo,
        provider=provider,
        user=agent_user,
    )


def test_delete__ok():

    """ Provider without agents is deleted """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = _create_provider(account)
    service = AIProviderService(user=owner, instance=provider)

    # act
    service.delete()

    # assert
    assert not AIProvider.objects.filter(id=provider.id).exists()


def test_delete__used_by_agent__raise_exception():

    """ Provider used by an agent cannot be deleted """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = _create_provider(account)
    _create_agent(account=account, provider=provider)
    service = AIProviderService(user=owner, instance=provider)

    # act
    with pytest.raises(AIProviderInUseException) as ex:
        service.delete()

    # assert
    assert str(ex.value.message) == str(MSG_AI_0005)
    assert AIProvider.objects.filter(id=provider.id).exists()


def test_delete__soft_deleted_agent__ok():

    """ Soft-deleted agents do not block provider deletion """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = _create_provider(account)
    agent = _create_agent(account=account, provider=provider)
    agent.delete()
    service = AIProviderService(user=owner, instance=provider)

    # act
    service.delete()

    # assert
    assert not AIProvider.objects.filter(id=provider.id).exists()
