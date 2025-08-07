from typing_extensions import Literal


class OpenAiModel:

    GPT_35_turbo = 'gpt-3.5-turbo'
    GPT_4_turbo_preview = 'gpt-4-1106-preview'
    GPT_4 = 'gpt-4'

    CHOICES = (
        (GPT_35_turbo, GPT_35_turbo),
        (GPT_4_turbo_preview, 'gpt-4-turbo-preview'),
        (GPT_4, GPT_4),
    )
    LITERALS = Literal[
        GPT_35_turbo,
        GPT_4_turbo_preview,
        GPT_4
    ]


class OpenAIRole:

    USER = 'user'
    SYSTEM = 'system'
    ASSISTANT = 'assistant'

    CHOICES = (
        (USER, USER),
        (SYSTEM, SYSTEM),
        (ASSISTANT, ASSISTANT),
    )


class OpenAIPromptTarget:

    GET_STEPS = 'get_steps'

    CHOICES = (
        (GET_STEPS, 'Get template steps'),
    )
