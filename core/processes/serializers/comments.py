from rest_framework import serializers
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)


class CommentCreateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    text = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    attachments = serializers.ListField(
        child=serializers.IntegerField(allow_null=False, min_value=1),
        required=False,
        allow_null=True,
        allow_empty=True,
    )

    def validate_text(self, value):
        if not value:
            return None
        elif isinstance(value, str):
            if not value.strip():
                return None
        return value

    def validate_attachments(self, value):
        if not value:
            return None
        return value


class CommentReactionSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    value = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
        max_length=10
    )
