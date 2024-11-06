from rest_framework import serializers
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin


class WebHookSubscribeSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    url = serializers.URLField(required=True)
