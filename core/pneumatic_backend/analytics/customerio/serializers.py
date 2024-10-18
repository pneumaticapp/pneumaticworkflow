from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    Serializer,
    CharField
)
from pneumatic_backend.generics.serializers import (
    CustomValidationErrorMixin
)

UserModel = get_user_model()


class WebHookIdSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    id = CharField(required=True, max_length=100)


class WebHookDataSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    identifiers = WebHookIdSerializer()


class WebHookSerializer(
    CustomValidationErrorMixin,
    Serializer
):

    metric = CharField(required=True, max_length=100)
    data = WebHookDataSerializer()
