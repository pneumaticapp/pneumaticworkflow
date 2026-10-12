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
        example='group-and-1',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    operator = DocChoiceField(
        choices=FieldSetRuleOperator.CHOICES,
        example=FieldSetRuleOperator.SUM_EQUAL,
        help_text=(
            'How the sum of `fields` is compared to '
            '`value`: `sum_equal`, `sum_greater_than`, '
            'or `sum_less_than`.'
        ),
    )
    value = DocCharField(
        max_length=200,
        required=False,
        allow_null=True,
        allow_blank=True,
        example='10',
        help_text=(
            'Number the summed field values are compared '
            'against.'
        ),
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
        example='group-or-1',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    groups_and = FieldSetTemplateRuleGroupAndSerializer(
        many=True,
        help_text=(
            'AND conditions inside this OR branch. '
            'All must be true for the branch to pass.'
        ),
    )


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
        example='ruleset-1',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    message = DocCharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        example='Sum must equal 10',
        help_text=(
            'Error shown when the ruleset conditions are '
            'not met.'
        ),
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
        help_text=(
            'Evaluation order among fieldset rulesets. '
            'Starts at 0.'
        ),
    )
    fields = RelatedApiNameListField(
        default=list,
        example=['amount'],
        help_text='`api_name` list of fields included in the sum.',
    )
    groups_or = FieldSetTemplateRuleGroupOrSerializer(
        many=True,
        help_text=(
            'OR branches. The ruleset passes if any '
            'branch is true.'
        ),
    )
