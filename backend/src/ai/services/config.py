from typing import Dict
from src.ai.services.entities import ProviderConfig
from src.ai.services.handlers import (
    AnthropicHandler,
    CursorHandler,
    GeminiHandler,
    OpenAIHandler,
)
from src.ai.enums import AIVendor


AI_VENDORS_CONFIG: Dict[str, ProviderConfig] = {
    AIVendor.OPENAI: ProviderConfig(
        name='OpenAI',
        slug=AIVendor.OPENAI,
        base_url='https://api.openai.com/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.OPENROUTER: ProviderConfig(
        name='OpenRouter',
        slug=AIVendor.OPENROUTER,
        base_url='https://openrouter.ai/api/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.ANTHROPIC: ProviderConfig(
        name='Anthropic',
        slug=AIVendor.ANTHROPIC,
        base_url='https://api.anthropic.com/v1',
        handler=AnthropicHandler,
        endpoints={'chat': 'messages'},
    ),
    AIVendor.GEMINI: ProviderConfig(
        name='Gemini',
        slug=AIVendor.GEMINI,
        base_url='https://generativelanguage.googleapis.com/v1beta',
        handler=GeminiHandler,
        endpoints={'chat': 'models/{model}:generateContent'},
    ),
    AIVendor.GROQ: ProviderConfig(
        name='Groq',
        slug=AIVendor.GROQ,
        base_url='https://api.groq.com/openai/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.XAI: ProviderConfig(
        name='xAI',
        slug=AIVendor.XAI,
        base_url='https://api.x.ai/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.TOGETHER: ProviderConfig(
        name='Together',
        slug=AIVendor.TOGETHER,
        base_url='https://api.together.xyz/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.FIREWORKS: ProviderConfig(
        name='Fireworks',
        slug=AIVendor.FIREWORKS,
        base_url='https://api.fireworks.ai/inference/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.DEEPSEEK: ProviderConfig(
        name='DeepSeek',
        slug=AIVendor.DEEPSEEK,
        base_url='https://api.deepseek.com',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.MISTRAL: ProviderConfig(
        name='Mistral',
        slug=AIVendor.MISTRAL,
        base_url='https://api.mistral.ai/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.CEREBRAS: ProviderConfig(
        name='Cerebras',
        slug=AIVendor.CEREBRAS,
        base_url='https://api.cerebras.ai/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.PERPLEXITY: ProviderConfig(
        name='Perplexity',
        slug=AIVendor.PERPLEXITY,
        base_url='https://api.perplexity.ai',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.HUGGINGFACE: ProviderConfig(
        name='Hugging Face',
        slug=AIVendor.HUGGINGFACE,
        base_url='https://router.huggingface.co/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.SAMBANOVA: ProviderConfig(
        name='SambaNova',
        slug=AIVendor.SAMBANOVA,
        base_url='https://api.sambanova.ai/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.NVIDIA_NIM: ProviderConfig(
        name='NVIDIA NIM',
        slug=AIVendor.NVIDIA_NIM,
        base_url='https://integrate.api.nvidia.com/v1',
        handler=OpenAIHandler,
        endpoints={},
    ),
    AIVendor.CURSOR: ProviderConfig(
        name='Cursor',
        slug=AIVendor.CURSOR,
        base_url='https://api.cursor.com/v1',
        handler=CursorHandler,
        endpoints={},
    ),
}
