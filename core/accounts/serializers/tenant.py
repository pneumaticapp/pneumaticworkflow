from pneumatic_backend.accounts.models import Account
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
)
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin
from pneumatic_backend.generics.fields import TimeStampField


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
        max_length=255
    )
    date_joined_tsp = TimeStampField(source='date_joined', read_only=True)
