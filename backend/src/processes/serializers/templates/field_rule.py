from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from src.generics.fields import AccountOnlyRelatedApiNameField
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)


class FieldTemplateRuleGroupAndSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateRuleGroupAnd
        fields = (
            'api_name',
            'field',
            'operator',
            'value',
        )

    api_name = CharField(max_length=200, required=False)
    field = AccountOnlyRelatedApiNameField(
        queryset=FieldTemplate.objects.all(),
    )


class FieldTemplateRuleGroupOrSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateRuleGroupOr
        fields = (
            'api_name',
            'group_and',
        )

    api_name = CharField(max_length=200, required=False)
    group_and = FieldTemplateRuleGroupAndSerializer(
        many=True,
        source='groups_and',
    )


class FieldTemplateRuleSetSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateRuleSet
        fields = (
            'api_name',
            'type',
            'message',
            'order',
            'group_or',
        )

    api_name = CharField(max_length=200, required=False)
    group_or = FieldTemplateRuleGroupOrSerializer(
        many=True,
        source='groups_or',
    )
