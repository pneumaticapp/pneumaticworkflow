from django.utils import timezone
from rest_framework import serializers
from src.generics.fields import TimeStampField
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.messages.workflow import (
    MSG_PW_0051,
)


class DueDateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    due_date_tsp = TimeStampField(
        required=True,
        allow_null=False
    )

    def validate_due_date_tsp(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(MSG_PW_0051)
        return value
