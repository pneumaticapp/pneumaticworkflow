from rest_framework.serializers import (
    CharField,
    IntegerField,
    ModelSerializer,
)

from src.generics.fields import TimeStampField
from src.datasets.models import Dataset, DatasetItem
from src.generics.mixins.serializers import CustomValidationErrorMixin


class DatasetItemSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = DatasetItem
        fields = (
            'id',
            'value',
            'order',
        )

    id = IntegerField(required=False)
    value = CharField(max_length=200)
    order = IntegerField(default=0)


class DatasetListSerializer(ModelSerializer):

    class Meta:
        model = Dataset
        fields = (
            'id',
            'name',
            'description',
            'date_created_tsp',
            'items_count',
        )

    id = IntegerField(read_only=True)
    name = CharField(max_length=200)
    description = CharField(allow_blank=True, default='')
    date_created_tsp = TimeStampField(
        source='date_created',
        read_only=True,
    )
    items_count = IntegerField(read_only=True)


class DatasetSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = Dataset
        fields = (
            'id',
            'name',
            'description',
            'date_created_tsp',
            'items',
        )

    id = IntegerField(required=False)
    name = CharField(max_length=200)
    description = CharField(allow_blank=True, default='')
    date_created_tsp = TimeStampField(
        source='date_created',
        read_only=True,
    )
    items = DatasetItemSerializer(many=True, required=False, default=list)
