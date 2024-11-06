from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    Serializer,
    IntegerField,
    EmailField
)
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)

UserModel = get_user_model()


class TaskPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    user_id = IntegerField(required=True)


class TaskGuestPerformerSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    email = EmailField(required=True)

    def validate_email(self, value):
        return value.lower()
