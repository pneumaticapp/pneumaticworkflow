from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    ModelSerializer,
    Serializer,
    URLField,
)

from src.ai.models import AIAgent, AIProvider
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
            'is_active',
        )

    id = IntegerField(read_only=True)
    name = CharField(max_length=255)
    base_url = URLField(max_length=1024)
    api_key = CharField(write_only=True)
    is_active = BooleanField(required=False, default=True)


class AIModelSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    name = CharField()
    slug = CharField()


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

    id = IntegerField(read_only=True)
    name = CharField(max_length=255)
    photo = URLField(
        max_length=1024,
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    is_active = BooleanField()
    provider_id = IntegerField()
    model = CharField(max_length=200)
    system_prompt = CharField(default='')
