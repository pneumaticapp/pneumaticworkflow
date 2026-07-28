from rest_framework.serializers import ModelSerializer

from src.ai.models import AIAgent
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
