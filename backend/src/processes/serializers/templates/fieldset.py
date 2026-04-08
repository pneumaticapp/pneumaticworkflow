from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.fields import TimeStampField
from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.models.templates.fieldset import FieldsetTemplateRule


class FieldsetTemplateRuleSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplateRule
        fields = (
            'id',
            'name',
            'type',
            'value',
            'date_created_tsp',
        )

    id = IntegerField(read_only=True)
    date_created_tsp = TimeStampField(
        source='date_created',
        read_only=True,
    )
