from rest_framework import serializers

from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)


class CommentCreateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    text = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def validate_text(self, value):
        if not value:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value


class CommentReactionSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    value = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
        max_length=10,
    )
