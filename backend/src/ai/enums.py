from typing_extensions import Literal


class AIVendor:

    OPENAI = 'openai'
    OPENROUTER = 'openrouter'
    ANTHROPIC = 'anthropic'
    GEMINI = 'gemini'
    GROQ = 'groq'
    XAI = 'xai'
    TOGETHER = 'together'
    FIREWORKS = 'fireworks'
    DEEPSEEK = 'deepseek'
    MISTRAL = 'mistral'
    CEREBRAS = 'cerebras'
    PERPLEXITY = 'perplexity'
    HUGGINGFACE = 'huggingface'
    SAMBANOVA = 'sambanova'
    NVIDIA_NIM = 'nvidia_nim'
    CURSOR = 'cursor'
    CUSTOM = 'custom'

    CHOICES = (
        (OPENAI, 'OpenAI'),
        (OPENROUTER, 'OpenRouter'),
        (ANTHROPIC, 'Anthropic'),
        (GEMINI, 'Gemini'),
        (GROQ, 'Groq'),
        (XAI, 'xAI'),
        (TOGETHER, 'Together'),
        (FIREWORKS, 'Fireworks'),
        (DEEPSEEK, 'DeepSeek'),
        (MISTRAL, 'Mistral'),
        (CEREBRAS, 'Cerebras'),
        (PERPLEXITY, 'Perplexity'),
        (HUGGINGFACE, 'Hugging Face'),
        (SAMBANOVA, 'SambaNova'),
        (NVIDIA_NIM, 'NVIDIA NIM'),
        (CURSOR, 'Cursor'),
    )

    LITERALS = Literal[
        OPENAI,
        OPENROUTER,
        ANTHROPIC,
        GEMINI,
        GROQ,
        XAI,
        TOGETHER,
        FIREWORKS,
        DEEPSEEK,
        MISTRAL,
        CEREBRAS,
        PERPLEXITY,
        HUGGINGFACE,
        SAMBANOVA,
        NVIDIA_NIM,
        CURSOR,
        CUSTOM,
    ]


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
        GPT_4,
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


class AIAgentActionType:

    TASK_IN_PROGRESS = 'task_in_progress'
    READING_DESCRIPTION = 'reading_description'
    REQUEST = 'request'
    ERROR = 'error'
    MENTION_IN_PROGRESS = 'mention_in_progress'

    CHOICES = (
        (TASK_IN_PROGRESS, 'Task in progress'),
        (READING_DESCRIPTION, 'Reading task description'),
        (REQUEST, 'Request'),
        (ERROR, 'Error'),
        (MENTION_IN_PROGRESS, 'Mention in progress'),
    )
    LITERALS = Literal[
        TASK_IN_PROGRESS,
        READING_DESCRIPTION,
        REQUEST,
        ERROR,
        MENTION_IN_PROGRESS,
    ]
