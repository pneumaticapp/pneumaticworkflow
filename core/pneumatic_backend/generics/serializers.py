from datetime import datetime, time

from django.utils import timezone
from rest_framework.fields import DateTimeField
from pneumatic_backend.generics.fields import TimeStampField
from rest_framework.serializers import Serializer

from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin
)


def get_default_date_from():
    return datetime.combine(timezone.now(), time.min)


def get_default_date_to():
    return timezone.now()


class DateTimeRangeSerializer(CustomValidationErrorMixin, Serializer):
    date_to = DateTimeField(default=get_default_date_to)
    date_from = DateTimeField(default=get_default_date_from)
    date_to_tsp = TimeStampField(required=False, allow_null=True)
    date_from_tsp = TimeStampField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get('date_to_tsp') is not None:
            attrs['date_to'] = attrs['date_to_tsp']
        if attrs.get('date_from_tsp') is not None:
            attrs['date_from'] = attrs['date_from_tsp']
        return attrs
