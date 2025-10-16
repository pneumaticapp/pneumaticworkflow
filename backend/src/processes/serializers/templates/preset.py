from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    IntegerField,
    ModelSerializer,
)

from src.generics.fields import TimeStampField
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.enums import PresetType
from src.processes.models.templates.preset import (
    TemplatePreset,
    TemplatePresetField,
)


class TemplatePresetFieldSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = TemplatePresetField
        fields = (
            'order',
            'width',
            'api_name',
        )

    order = IntegerField(min_value=0)
    width = IntegerField(min_value=1, max_value=1000)
    api_name = CharField(max_length=200)


class TemplatePresetSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):
    class Meta:
        model = TemplatePreset
        fields = (
            'id',
            'name',
            'author',
            'date_created_tsp',
            'is_default',
            'type',
            'fields',
        )

    name = CharField(max_length=200, required=True)
    author = IntegerField(source='author_id', read_only=True)
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    is_default = BooleanField(default=False)
    type = ChoiceField(choices=PresetType.CHOICES)
    fields = TemplatePresetFieldSerializer(many=True, required=True)
