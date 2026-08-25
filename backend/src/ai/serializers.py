from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
)

from src.ai.models import AIAgent, AIProvider
from src.generics.fields import (
    DocBooleanField,
    DocCharField,
    DocIntegerField,
    DocSerializerMethodField,
    DocURLField,
)
from src.generics.mixins.serializers import CustomValidationErrorMixin


class AIProviderSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = AIProvider
        fields = (
            'id',
            'name',
            'base_url',
            'api_key',
            'api_key_prefix',
            'is_active',
        )

    id = DocIntegerField(
        read_only=True,
        help_text='Unique identifier of the AI provider',
        example=1,
    )
    name = DocCharField(
        max_length=255,
        help_text='Display name of the provider',
        example='OpenRouter',
    )
    base_url = DocURLField(
        max_length=1024,
        help_text='Base URL of the provider API',
        example='https://openrouter.ai/api/v1',
    )
    api_key = DocCharField(
        write_only=True,
        help_text=(
            'Secret API key for the provider. '
            'Write-only — never returned in responses'
        ),
        example='sk-or-v1-example',
    )
    is_active = DocBooleanField(
        required=False,
        default=True,
        help_text='Whether the provider is enabled',
        example=True,
    )
    api_key_prefix = DocSerializerMethodField(
        help_text='Secret API key prefix for the provider',
        example='sk-or-v1-744afb981...',
    )

    def get_api_key_prefix(self, obj) -> str:
        length = AIProvider.API_KEY_PREFIX_DISPLAY_LENGTH
        return obj.api_key[:length]


class AIModelSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    name = DocCharField(
        help_text='Human-readable model name',
        example='GPT-4o',
    )
    slug = DocCharField(
        help_text='Model identifier in OpenRouter-style format',
        example='openai/gpt-4o',
    )


class AIAgentSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = AIAgent
        fields = (
            'id',
            'name',
            'photo',
            'is_active',
            'provider_id',
            'model',
            'system_prompt',
        )

    id = DocIntegerField(
        read_only=True,
        help_text='Unique identifier of the AI agent',
        example=1,
    )
    name = DocCharField(
        max_length=255,
        help_text='Display name of the agent',
        example='Research assistant',
    )
    photo = DocURLField(
        max_length=1024,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='URL of the agent avatar',
        example='https://example.com/images/assistant.jpg',
    )
    is_active = DocBooleanField(
        help_text='Whether the agent is enabled',
        example=True,
    )
    provider_id = DocIntegerField(
        help_text='Identifier of the AI provider this agent uses',
        example=1,
    )
    model = DocCharField(
        max_length=200,
        help_text='OpenRouter-style model slug',
        example='openai/gpt-4o',
    )
    system_prompt = DocCharField(
        default='',
        help_text='System instructions that define the agent behavior',
        example='You are a helpful research assistant.',
    )
