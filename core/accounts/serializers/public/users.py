from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    ModelSerializer
)

UserModel = get_user_model()


class PublicUserSerializer(ModelSerializer):

    class Meta:
        model = UserModel
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'status',
        )
