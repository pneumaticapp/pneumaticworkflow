from django.contrib.auth import get_user_model
from rest_framework import serializers

from src.accounts.models import APIKey
from src.generics.mixins.serializers import AdditionalValidationMixin

UserModel = get_user_model()


class APIKeyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = (
            'id',
            'name',
            'prefix',
            'date_created',
            'last_used_at',
            'expires_at',
            'is_active',
        )


class APIKeyCreateSerializer(
    AdditionalValidationMixin,
    serializers.Serializer,
):
    name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
    )


class APIKeyResponseSerializer(APIKeyListSerializer):
    key = serializers.CharField()

    class Meta(APIKeyListSerializer.Meta):
        fields = (*APIKeyListSerializer.Meta.fields, 'key')


class APIKeyRevokeSerializer(
    AdditionalValidationMixin,
    serializers.Serializer,
):
    api_key_id = serializers.IntegerField()
