from rest_framework import serializers

from src.accounts.models import APIKey
from src.generics.mixins.serializers import AdditionalValidationMixin


class APIKeySerializer(
    AdditionalValidationMixin,
    serializers.ModelSerializer,
):
    """Single serializer for list, retrieve and create."""

    prefix = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'GET':
            self.fields.pop('token', None)

    class Meta:
        model = APIKey
        fields = (
            'id',
            'name',
            'prefix',
            'token',
            'date_created',
            'last_used_at',
            'expires_at',
            'is_active',
        )
        read_only_fields = (
            'id',
            'prefix',
            'token',
            'date_created',
            'last_used_at',
            'expires_at',
            'is_active',
        )

    def get_prefix(self, obj: APIKey) -> str:
        n = APIKey.API_KEY_PREFIX_DISPLAY_LENGTH
        return obj.token[:n] if obj.token else ''
