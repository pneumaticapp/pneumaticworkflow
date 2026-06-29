from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from src.accounts.models import (
    APIKey,
)

UserModel = get_user_model()


class APIKeyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = (
            'id',
            'name',
            'key',
        )


class UserAPIKeySerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = (
            'first_name',
            'last_name',
            'email',
            'is_admin',
            'is_account_owner',
            'api_key',
            'type',
            'status',
        )

    api_key = serializers.SerializerMethodField()

    def get_api_key(self, obj) -> str:
        try:
            return obj.apikey.key
        except ObjectDoesNotExist:
            return None
