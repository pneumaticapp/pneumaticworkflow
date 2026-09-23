from typing_extensions import Literal


class AIVendor:

    OPENAI = 'openai'
    OPENROUTER = 'openrouter'
    ANTHROPIC = 'anthropic'
    GEMINI = 'gemini'
    GROQ = 'groq'
    DEEPSEEK = 'deepseek'
    CUSTOM = 'custom'

    CHOICES = (
        (OPENAI, 'OpenAI'),
        (OPENROUTER, 'OpenRouter'),
        (ANTHROPIC, 'Anthropic'),
        (GEMINI, 'Gemini'),
        (GROQ, 'Groq'),
        (DEEPSEEK, 'DeepSeek'),
    )

    LITERALS = Literal[
        OPENAI,
        OPENROUTER,
        ANTHROPIC,
        GEMINI,
        GROQ,
        DEEPSEEK,
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
    TASK_COMPLETED = 'task_completed'
    AI_REQUEST = 'ai_request'
    AI_RESPONSE = 'ai_response'
    READING_DESCRIPTION = 'reading_description'
    REQUEST = 'request'
    ERROR = 'error'
    MENTION_IN_PROGRESS = 'mention_in_progress'

    CHOICES = (
        (AI_RESPONSE, 'AI response'),
        (AI_REQUEST, 'AI request user message'),
        (TASK_IN_PROGRESS, 'Task in progress'),
        (TASK_COMPLETED, 'Task completed'),
        (READING_DESCRIPTION, 'Reading task description'),
        (REQUEST, 'Request'),
        (ERROR, 'Error'),
        (MENTION_IN_PROGRESS, 'Mention in progress'),
    )
    LITERALS = Literal[
        TASK_IN_PROGRESS,
        TASK_COMPLETED,
        READING_DESCRIPTION,
        AI_RESPONSE,
        AI_REQUEST,
        REQUEST,
        ERROR,
        MENTION_IN_PROGRESS,
    ]
