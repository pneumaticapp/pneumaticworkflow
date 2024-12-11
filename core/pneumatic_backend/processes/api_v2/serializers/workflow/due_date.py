from django.utils import timezone
from rest_framework import serializers
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from pneumatic_backend.processes.messages.workflow import (
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
