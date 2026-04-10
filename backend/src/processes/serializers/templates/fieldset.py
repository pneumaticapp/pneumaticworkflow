from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
)

from src.generics.mixins.serializers import CustomValidationErrorMixin
from src.processes.serializers.templates.field import FieldTemplateSerializer
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)


class FieldsetTemplateRuleSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplateRule
        fields = (
            'id',
            'type',
            'value',
            'api_name',
        )

    id = IntegerField(read_only=True)


class FieldsetTemplateSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldsetTemplate
        fields = (
            'id',
            'name',
            'description',
            'rules',
            'fields',
            'api_name',
        )

    id = IntegerField(read_only=True)
    rules = FieldsetTemplateRuleSerializer(
        many=True,
        required=False,
        default=list,
    )
    fields = FieldTemplateSerializer(
        many=True,
        required=False,
        default=list,
    )
