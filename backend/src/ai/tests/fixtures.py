import string
from typing import Optional

from django.utils.crypto import get_random_string

from src.ai.enums import (
    OpenAiModel,
    OpenAIPromptTarget,
    OpenAIRole,
)
from src.ai.models import (
    AIAgent,
    AIProvider,
    OpenAiMessage,
    OpenAiPrompt,
)
from src.processes.tests.fixtures import (
    create_test_admin,
)


def create_test_prompt(
    model: OpenAiModel.LITERALS = OpenAiModel.GPT_35_turbo,
    is_active: bool = True,
    messages_count: int = 1,
    target: str = OpenAIPromptTarget.GET_STEPS,
    content: str = 'Some {{ user_description }} text',
) -> OpenAiPrompt:

    prompt = OpenAiPrompt.objects.create(
        model=model,
        target=target,
        is_active=is_active,
    )
    for order in range(1, messages_count + 1):
        OpenAiMessage.objects.create(
            role=OpenAIRole.USER,
            content=content,
            prompt=prompt,
            is_active=True,
            order=order,
        )
    return prompt


def create_test_provider(
    account,
    name: str = 'OpenRouter',
    base_url: str = 'https://openrouter.ai/api/v1',
    api_key: str = 'sk-or-v1-example',
    is_active: bool = True,
) -> AIProvider:
    provider = AIProvider(
        account=account,
        name=name,
        base_url=base_url,
        is_active=is_active,
    )
    provider.api_key = api_key
    provider.save()
    return provider


def create_test_agent(
    account,
    provider: Optional[AIProvider] = None,
    name: str = 'Research assistant',
    model: str = 'openai/gpt-4o',
    system_prompt: str = 'You are helpful.',
    is_active: bool = True,
    photo: Optional[str] = None,
) -> AIAgent:
    if provider is None:
        provider = create_test_provider(account=account)
    salt = get_random_string(
        length=20,
        allowed_chars=string.ascii_letters + string.digits,
    )
    email = f'ai-agent-{salt}@pneumatic.app'
    agent_user = create_test_admin(
        account=account,
        email=email,
        first_name=name,
        is_ai=True,
    )
    return AIAgent.objects.create(
        account=account,
        name=name,
        model=model,
        system_prompt=system_prompt,
        is_active=is_active,
        photo=photo,
        provider=provider,
        user=agent_user,
    )
