from rest_framework import serializers
from rest_framework.serializers import ValidationError

from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.messages.workflow import MSG_PW_0047


class CommentCreateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    text = serializers.CharField(
        required=True,
        allow_null=False,
        allow_blank=True,
    )

    def validate_text(self, value):
        if not value.strip():
            raise ValidationError(MSG_PW_0047)
        return value.strip()


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
