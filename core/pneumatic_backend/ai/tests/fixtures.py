from pneumatic_backend.ai.models import (
    OpenAiPrompt,
    OpenAiMessage,
)
from pneumatic_backend.ai.enums import (
    OpenAIPromptTarget,
    OpenAIRole,
    OpenAiModel,
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
