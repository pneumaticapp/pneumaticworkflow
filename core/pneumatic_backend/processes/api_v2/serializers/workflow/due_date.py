from django.utils import timezone
from rest_framework import serializers
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0051,
    MSG_PW_0069,
)


class DueDateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    due_date = serializers.DateTimeField(
        required=False,
        allow_null=False
    )
    due_date_tsp = TimeStampField(
        required=False,
        allow_null=False
    )

    def validate_due_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(MSG_PW_0051)
        return value

    def validate_due_date_tsp(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(MSG_PW_0051)
        return value

    def validate(self, data):
        if (
            'due_date' not in data and
            'due_date_tsp' not in data
        ):
            raise serializers.ValidationError(MSG_PW_0069)
        data['due_date'] = data.get('due_date_tsp', data.get('due_date'))
        return data
