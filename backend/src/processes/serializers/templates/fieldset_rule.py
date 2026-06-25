from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from src.generics.fields import (
    RelatedApiNameListField,
)
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.models.templates.fieldset import (
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
)


class FieldSetTemplateRuleGroupAndSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldSetTemplateRuleGroupAnd
        fields = (
            'api_name',
            'operator',
            'value',
        )

    api_name = CharField(max_length=200, required=False)


class FieldSetTemplateRuleGroupOrSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldSetTemplateRuleGroupOr
        fields = (
            'api_name',
            'group_and',
        )

    api_name = CharField(max_length=200, required=False)
    group_and = FieldSetTemplateRuleGroupAndSerializer(
        many=True,
        source='groups_and',
    )


class FieldSetTemplateRuleSetSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldSetTemplateRuleSet
        fields = (
            'api_name',
            'type',
            'message',
            'order',
            'fields',
            'group_or',
        )

    api_name = CharField(max_length=200, required=False)
    fields = RelatedApiNameListField(
        default=list,
    )
    group_or = FieldSetTemplateRuleGroupOrSerializer(
        many=True,
        source='groups_or',
    )
