from rest_framework.serializers import ModelSerializer

from src.generics.fields import (
    DocCharField,
    DocChoiceField,
    DocIntegerField,
    RelatedApiNameListField,
)
from src.generics.mixins.serializers import (
    CustomValidationErrorMixin,
)
from src.processes.enums import FieldSetRuleOperator
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

    api_name = DocCharField(
        max_length=200,
        required=False,
        example='fieldset-rule-group-and-1',
    )
    operator = DocChoiceField(
        choices=FieldSetRuleOperator.CHOICES,
        example=FieldSetRuleOperator.SUM_EQUAL,
    )
    value = DocCharField(
        max_length=200,
        required=False,
        allow_null=True,
        allow_blank=True,
        example='10',
    )


class FieldSetTemplateRuleGroupOrSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldSetTemplateRuleGroupOr
        fields = (
            'api_name',
            'groups_and',
        )

    api_name = DocCharField(
        max_length=200,
        required=False,
        example='fieldset-rule-group-or-1',
    )
    groups_and = FieldSetTemplateRuleGroupAndSerializer(many=True)


class FieldSetTemplateRuleSetSerializer(
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldSetTemplateRuleSet
        fields = (
            'api_name',
            'message',
            'order',
            'fields',
            'groups_or',
        )

    api_name = DocCharField(
        max_length=200,
        required=False,
        example='fieldset-ruleset-1',
    )
    message = DocCharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        example='Sum must equal 10',
        help_text='Custom error message for type="validator"',
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
    )
    fields = RelatedApiNameListField(
        default=list,
        example=['amount'],
    )
    groups_or = FieldSetTemplateRuleGroupOrSerializer(many=True)
