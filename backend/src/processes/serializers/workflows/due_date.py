from rest_framework import serializers
from src.generics.fields import TimeStampField
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)


class DueDateSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    due_date_tsp = TimeStampField(
        required=True,
        allow_null=False
    )
