import pytz
from datetime import datetime
from typing import Union
from django.conf import settings
from rest_framework.utils import html
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.generics.messages import (
    MSG_GE_0002,
    MSG_GE_0007,
)
from pneumatic_backend.accounts.enums import (
    UserDateFormat,
)


class AccountPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):

    def _get_account(self) -> Account:
        account = self.context.get('account')
        if account is None:
            request = self.context.get('request')
            if request:
                account = request.user.account
        if not account:
            raise Exception(
                'Account not provided for AccountPrimaryKeyRelatedField'
            )
        return account

    def get_queryset(self):
        queryset = super().get_queryset()
        account = self._get_account()
        if account is None or queryset is None:
            raise Exception(MSG_GE_0002)
        return queryset.filter(account=account)


class AnyField(serializers.Field):

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class RelatedListField(serializers.ListField):

    def to_representation(self, objects):
        """
        List of objects -> List of objects ids.
        """
        return [
            self.child.to_representation(item.id)
            for item in objects.all()
        ]


class CommaSeparatedListField(serializers.ListField):

    def get_value(self, dictionary):
        if self.field_name not in dictionary:
            if getattr(self.root, 'partial', False):
                return empty
        if html.is_html_input(dictionary):
            val = dictionary.get(self.field_name, '')
            # Split result by comma
            val = val.split(',') if val else []
            if len(val) > 0:
                return val
            return html.parse_html_list(
                dictionary,
                prefix=self.field_name,
                default=empty
            )
        return dictionary.get(self.field_name, empty)


class TimeStampField(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return None
        return value.timestamp()

    def to_internal_value(self, value: Union[float, int]):
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise ValidationError(detail=MSG_GE_0007)

        elif not isinstance(value, int) and not isinstance(value, float):
            raise ValidationError(detail=MSG_GE_0007)

        tz = pytz.timezone(settings.TIME_ZONE)
        return datetime.fromtimestamp(value, tz=tz)


class DateFormatField(serializers.ChoiceField):

    def __init__(self, **kwargs):
        super().__init__(
            choices=UserDateFormat.API_CHOICES,
            **kwargs
        )

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return UserDateFormat.MAP_TO_PYTHON[value]

    def to_representation(self, value):
        value = str(value)
        return UserDateFormat.MAP_TO_API[value]
