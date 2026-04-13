from typing_extensions import Literal


class OpenAiModel:

    GPT_35_turbo = 'gpt-3.5-turbo'
    GPT_4_turbo_preview = 'gpt-4-1106-preview'
    GPT_4 = 'gpt-4'
    GPT_4o = 'gpt-4o'
    GPT_4o_mini = 'gpt-4o-mini'
    GPT_41 = 'gpt-4.1'
    GPT_41_mini = 'gpt-4.1-mini'
    GPT_41_nano = 'gpt-4.1-nano'
    GPT_5 = 'gpt-5'
    GPT_5_mini = 'gpt-5-mini'
    O3 = 'o3'
    O4_mini = 'o4-mini'

    CHOICES = (
        (GPT_41_mini, GPT_41_mini + ' (recommended)'),
        (GPT_41, GPT_41),
        (GPT_41_nano, GPT_41_nano),
        (GPT_5, GPT_5),
        (GPT_5_mini, GPT_5_mini),
        (O3, O3),
        (O4_mini, O4_mini),
        (GPT_4o, GPT_4o),
        (GPT_4o_mini, GPT_4o_mini),
        (GPT_4, GPT_4),
        (GPT_35_turbo, GPT_35_turbo),
        (GPT_4_turbo_preview, 'gpt-4-turbo-preview'),
    )
    LITERALS = Literal[
        GPT_35_turbo,
        GPT_4_turbo_preview,
        GPT_4,
        GPT_4o,
        GPT_4o_mini,
        GPT_41,
        GPT_41_mini,
        GPT_41_nano,
        GPT_5,
        GPT_5_mini,
        O3,
        O4_mini,
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
    GET_TEMPLATE = 'get_template'

    CHOICES = (
        (GET_STEPS, 'Get template steps'),
        (GET_TEMPLATE, 'Get full template (JSON)'),
    )
