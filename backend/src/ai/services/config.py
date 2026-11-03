from typing import Dict
from src.ai.services.entities import ProviderConfig
from src.ai.services.handlers import (
    AnthropicHandler,
    GeminiHandler,
    OpenAIHandler,
    OpenRouterHandler,
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
        handler=OpenRouterHandler,
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
    AIVendor.DEEPSEEK: ProviderConfig(
        name='DeepSeek',
        slug=AIVendor.DEEPSEEK,
        base_url='https://api.deepseek.com',
        handler=OpenAIHandler,
        endpoints={},
    ),
}
