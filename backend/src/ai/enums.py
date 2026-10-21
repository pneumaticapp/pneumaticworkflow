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
    TASK_FAILED = 'task_failed'
    TASK_ATTEMPTS_EXCEEDED = 'task_attempts_exceeded'

    AI_REQUEST = 'ai_request'
    AI_RESPONSE = 'ai_response'
    READING_DESCRIPTION = 'reading_description'
    REQUEST_FAILED = 'request_failed'

    MENTION_IN_PROGRESS = 'mention_in_progress'
    MENTION_FAILED = 'mention_failed'
    MENTION_ATTEMPTS_EXCEEDED = 'mention_attempts_exceeded'
    MENTION_COMPLETED = 'mention_completed'

    CHOICES = (
        (AI_RESPONSE, 'AI response'),
        (AI_REQUEST, 'AI request user message'),
        (TASK_IN_PROGRESS, 'Task in progress'),
        (TASK_COMPLETED, 'Task completed'),
        (TASK_FAILED, 'Task failed'),
        (READING_DESCRIPTION, 'Reading task description'),
        (REQUEST_FAILED, 'Request failed'),
        (TASK_ATTEMPTS_EXCEEDED, 'Task attempts exceeded'),
        (MENTION_IN_PROGRESS, 'Mention in progress'),
        (MENTION_FAILED, 'Mention failed'),
        (MENTION_ATTEMPTS_EXCEEDED, 'Mention attempts exceeded'),
        (MENTION_COMPLETED, 'Mention completed'),
    )
    LITERALS = Literal[
        TASK_IN_PROGRESS,
        TASK_COMPLETED,
        TASK_FAILED,
        READING_DESCRIPTION,
        AI_RESPONSE,
        AI_REQUEST,
        REQUEST_FAILED,
        TASK_ATTEMPTS_EXCEEDED,
        MENTION_IN_PROGRESS,
        MENTION_FAILED,
        MENTION_ATTEMPTS_EXCEEDED,
        MENTION_COMPLETED,
    ]
