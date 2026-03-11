from rest_framework.serializers import (
    CharField,
    DateTimeField,
    IntegerField,
    ModelSerializer,
)

from src.processes.models.templates.dataset import Dataset, DatasetItem


class DatasetItemSerializer(ModelSerializer):

    class Meta:
        model = DatasetItem
        fields = (
            'id',
            'value',
            'order',
        )

    id = IntegerField(read_only=True)
    value = CharField(max_length=200)
    order = IntegerField(default=0)


class DatasetListSerializer(ModelSerializer):

    class Meta:
        model = Dataset
        fields = (
            'id',
            'name',
            'description',
            'date_created',
        )

    id = IntegerField(read_only=True)
    name = CharField(max_length=200)
    description = CharField(allow_blank=True, default='')
    date_created = DateTimeField(read_only=True)


class DatasetSerializer(ModelSerializer):

    class Meta:
        model = Dataset
        fields = (
            'id',
            'name',
            'description',
            'date_created',
            'items',
        )

    id = IntegerField(read_only=True)
    name = CharField(max_length=200)
    description = CharField(allow_blank=True, default='')
    date_created = DateTimeField(read_only=True)
    items = DatasetItemSerializer(many=True, read_only=True)
