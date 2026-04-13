from rest_framework.fields import CharField
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
    api_name = CharField(required=False, max_length=200)


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
            'order',
            'label_position',
            'layout',
            'rules',
            'fields',
            'api_name',
        )

    id = IntegerField(read_only=True)
    api_name = CharField(required=False, max_length=200)
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
