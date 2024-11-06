from django.contrib.auth import get_user_model
from rest_framework import serializers
from pneumatic_backend.accounts.models import (
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
