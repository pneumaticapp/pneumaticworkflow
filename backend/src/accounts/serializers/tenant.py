from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)

from src.accounts.models import Account
from src.generics.fields import TimeStampField
from src.generics.serializers import CustomValidationErrorMixin


class TenantSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = Account
        fields = (
            'id',
            'date_joined',
            'date_joined_tsp',
            'tenant_name',
        )
        read_only_fields = (
            'id',
            'date_joined',
            'date_joined_tsp',
        )

    tenant_name = CharField(
        allow_null=False,
        allow_blank=False,
        max_length=255,
    )
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
