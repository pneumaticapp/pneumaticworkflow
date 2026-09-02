from typing_extensions import Literal


class AIVendor:

    OPENAI = 'openai'
    OPENROUTER = 'openrouter'
    ANTHROPIC = 'anthropic'
    GEMINI = 'gemini'
    GROQ = 'groq'
    XAI = 'xai'
    AZURE_OPENAI = 'azure_openai'
    TOGETHER = 'together'
    FIREWORKS = 'fireworks'
    DEEPSEEK = 'deepseek'
    MISTRAL = 'mistral'
    CEREBRAS = 'cerebras'
    PERPLEXITY = 'perplexity'
    HUGGINGFACE = 'huggingface'
    SAMBANOVA = 'sambanova'
    NVIDIA_NIM = 'nvidia_nim'
    OPENAI_COMPATIBLE = 'openai_compatible'

    CHOICES = (
        (OPENAI, 'OpenAI'),
        (OPENROUTER, 'OpenRouter'),
        (ANTHROPIC, 'Anthropic'),
        (GEMINI, 'Gemini'),
        (GROQ, 'Groq'),
        (XAI, 'xAI'),
        (AZURE_OPENAI, 'Azure OpenAI'),
        (TOGETHER, 'Together'),
        (FIREWORKS, 'Fireworks'),
        (DEEPSEEK, 'DeepSeek'),
        (MISTRAL, 'Mistral'),
        (CEREBRAS, 'Cerebras'),
        (PERPLEXITY, 'Perplexity'),
        (HUGGINGFACE, 'Hugging Face'),
        (SAMBANOVA, 'SambaNova'),
        (NVIDIA_NIM, 'NVIDIA NIM'),
        (OPENAI_COMPATIBLE, 'OpenAI compatible'),
    )

    CODE_BY_HOST = {
        'api.openai.com': OPENAI,
        'openrouter.ai': OPENROUTER,
        'api.anthropic.com': ANTHROPIC,
        'generativelanguage.googleapis.com': GEMINI,
        'api.groq.com': GROQ,
        'api.x.ai': XAI,
        'openai.azure.com': AZURE_OPENAI,
        'api.together.ai': TOGETHER,
        'api.together.xyz': TOGETHER,
        'api.fireworks.ai': FIREWORKS,
        'api.deepseek.com': DEEPSEEK,
        'api.mistral.ai': MISTRAL,
        'api.cerebras.ai': CEREBRAS,
        'api.perplexity.ai': PERPLEXITY,
        'router.huggingface.co': HUGGINGFACE,
        'api.sambanova.ai': SAMBANOVA,
        'integrate.api.nvidia.com': NVIDIA_NIM,
    }

    NAME_BY_CODE = {
        OPENAI: 'OpenAI',
        OPENROUTER: 'OpenRouter',
        ANTHROPIC: 'Anthropic',
        GEMINI: 'Gemini',
        GROQ: 'Groq',
        XAI: 'xAI',
        AZURE_OPENAI: 'Azure OpenAI',
        TOGETHER: 'Together',
        FIREWORKS: 'Fireworks',
        DEEPSEEK: 'DeepSeek',
        MISTRAL: 'Mistral',
        CEREBRAS: 'Cerebras',
        PERPLEXITY: 'Perplexity',
        HUGGINGFACE: 'Hugging Face',
        SAMBANOVA: 'SambaNova',
        NVIDIA_NIM: 'NVIDIA NIM',
        OPENAI_COMPATIBLE: 'OpenAI compatible',
    }

    LITERALS = Literal[
        OPENAI,
        OPENROUTER,
        ANTHROPIC,
        GEMINI,
        GROQ,
        XAI,
        AZURE_OPENAI,
        TOGETHER,
        FIREWORKS,
        DEEPSEEK,
        MISTRAL,
        CEREBRAS,
        PERPLEXITY,
        HUGGINGFACE,
        SAMBANOVA,
        NVIDIA_NIM,
        OPENAI_COMPATIBLE,
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
