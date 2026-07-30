from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from src.ai.models import AIAgent, AIProviderConnection
from src.ai.providers import mask_api_key
from src.generics.mixins.serializers import CustomValidationErrorMixin


class AIAgentSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = AIAgent
        fields = (
            'id',
            'name',
            'model_slug',
            'system_prompt',
            'temperature',
            'max_tokens',
            'photo',
            'is_active',
        )
        read_only_fields = ('id',)


class AIProviderConnectionSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    """ The key is write-only: after saving, clients only ever see
        the mask. """

    api_key = serializers.CharField(write_only=True, trim_whitespace=True)
    api_key_mask = serializers.SerializerMethodField()

    class Meta:
        model = AIProviderConnection
        fields = (
            'id',
            'base_url',
            'api_key',
            'api_key_mask',
        )
        read_only_fields = ('id', 'api_key_mask')

    def get_api_key_mask(self, connection) -> str:
        return mask_api_key(connection.api_key)
