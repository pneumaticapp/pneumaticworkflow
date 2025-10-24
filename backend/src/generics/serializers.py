from datetime import datetime, time

from django.utils import timezone
from rest_framework.serializers import Serializer

from src.generics.fields import TimeStampField
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)


def get_default_date_from():
    return datetime.combine(timezone.now(), time.min)


def get_default_date_to():
    return timezone.now()


class DateTimeRangeSerializer(CustomValidationErrorMixin, Serializer):
    date_to_tsp = TimeStampField(default=get_default_date_to)
    date_from_tsp = TimeStampField(default=get_default_date_from)
