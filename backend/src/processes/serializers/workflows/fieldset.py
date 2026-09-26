from rest_framework import serializers

from src.generics.fields import (
    DocCharField,
    DocChoiceField,
    DocIntegerField,
    RelatedApiNameListField,
)
from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleOperator,
    LabelPosition,
)
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRuleGroupAnd,
    FieldSetRuleGroupOr,
    FieldSetRuleSet,
)
from src.processes.serializers.workflows.field import (
    TaskFieldEventSerializer,
    TaskFieldSerializer,
)


class FieldSetRuleGroupAndSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldSetRuleGroupAnd
        fields = (
            'api_name',
            'operator',
            'value',
        )

    api_name = DocCharField(
        read_only=True,
        example='fieldset-rule-group-and-1',
        help_text='Stable unique identifier.',
    )
    operator = DocChoiceField(
        read_only=True,
        choices=FieldSetRuleOperator.CHOICES,
        example=FieldSetRuleOperator.SUM_EQUAL,
        help_text=(
            'Comparison of the sum of the ruleset fields against `value`.'
        ),
    )
    value = DocCharField(
        read_only=True,
        example='100',
        help_text='Number the sum of the fields is compared against.',
    )


class FieldSetRuleGroupOrSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldSetRuleGroupOr
        fields = (
            'api_name',
            'groups_and',
        )

    api_name = DocCharField(
        read_only=True,
        example='fieldset-rule-group-or-1',
        help_text='Stable unique identifier.',
    )
    groups_and = FieldSetRuleGroupAndSerializer(
        many=True,
        read_only=True,
        help_text=(
            'AND conditions inside this OR branch. '
            'All must be true for the branch to pass.'
        ),
    )


class FieldSetRuleSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldSetRuleSet
        fields = (
            'api_name',
            'message',
            'order',
            'fields',
            'groups_or',
        )

    api_name = DocCharField(
        read_only=True,
        example='fieldset-ruleset-1',
        help_text='Stable unique identifier.',
    )
    # The model help_text still mentions a type="validator" copied over
    # from the deprecated flat rule; these models have no type at all.
    message = DocCharField(
        read_only=True,
        example='The sum of the fields must equal 100',
        help_text='Error shown when none of the OR branches passes.',
    )
    order = DocIntegerField(
        read_only=True,
        example=0,
        help_text=(
            'Evaluation order among the rulesets of the fieldset. '
            'Starts at 0.'
        ),
    )
    fields = RelatedApiNameListField(
        read_only=True,
        example=['field-1', 'field-2'],
        help_text=(
            '`api_name` list of the fieldset fields whose values are '
            'summed up.'
        ),
    )
    groups_or = FieldSetRuleGroupOrSerializer(
        many=True,
        read_only=True,
        help_text=(
            'OR branches. The ruleset passes if any branch is true.'
        ),
    )


class FieldSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldSet
        fields = (
            'id',
            'api_name',
            'name',
            'title',
            'description',
            'order',
            'label_position',
            'layout',
            'fields',
            'rulesets',
        )

    id = DocIntegerField(
        read_only=True,
        example=1,
        help_text='Fieldset id. Read-only.',
    )
    api_name = DocCharField(
        read_only=True,
        example='feedback-fieldset',
        help_text='Stable unique identifier.',
    )
    name = DocCharField(
        read_only=True,
        example='Feedback block',
        help_text='Internal name shown in the fieldset catalog.',
    )
    title = DocCharField(
        read_only=True,
        example='Feedback form',
        help_text=(
            'Heading displayed above the fieldset in the form.'
        ),
    )
    description = DocCharField(
        read_only=True,
        example='Leave a review about your order',
        help_text='Helper text shown under the fieldset heading.',
    )
    order = DocIntegerField(
        read_only=True,
        example=0,
        help_text=(
            'Display order among fieldsets on the same '
            'step. Starts at 0.'
        ),
    )
    label_position = DocChoiceField(
        read_only=True,
        choices=LabelPosition.CHOICES,
        example=LabelPosition.TOP,
        help_text=(
            'Where field labels are placed relative to '
            'inputs: `top` or `left`.'
        ),
    )
    layout = DocChoiceField(
        read_only=True,
        choices=FieldSetLayout.CHOICES,
        example=FieldSetLayout.VERTICAL,
        help_text=(
            'How fields are arranged: `vertical` or '
            '`horizontal`.'
        ),
    )
    fields = TaskFieldSerializer(
        many=True,
        help_text='Fields that belong to this fieldset.',
    )
    rulesets = FieldSetRuleSetSerializer(
        many=True,
        read_only=True,
        help_text=(
            'Sum-validation rules of the fieldset. '
            'Empty when the fieldset has no rules.'
        ),
    )


class FieldSetEventSerializer(serializers.ModelSerializer):

    """ Events and highlights show a snapshot, not the editor config,
        so neither the fieldset nor its fields carry rulesets. """

    class Meta:
        model = FieldSet
        fields = (
            'id',
            'api_name',
            'name',
            'title',
            'description',
            'order',
            'label_position',
            'layout',
            'fields',
        )

    id = DocIntegerField(
        read_only=True,
        example=1,
        help_text='Fieldset id. Read-only.',
    )
    api_name = DocCharField(
        read_only=True,
        example='feedback-fieldset',
        help_text='Stable unique identifier.',
    )
    name = DocCharField(
        read_only=True,
        example='Feedback block',
        help_text='Internal name shown in the fieldset catalog.',
    )
    title = DocCharField(
        read_only=True,
        example='Feedback form',
        help_text=(
            'Heading displayed above the fieldset in the form.'
        ),
    )
    description = DocCharField(
        read_only=True,
        example='Leave a review about your order',
        help_text='Helper text shown under the fieldset heading.',
    )
    order = DocIntegerField(
        read_only=True,
        example=0,
        help_text=(
            'Display order among fieldsets on the same '
            'step. Starts at 0.'
        ),
    )
    label_position = DocChoiceField(
        read_only=True,
        choices=LabelPosition.CHOICES,
        example=LabelPosition.TOP,
        help_text=(
            'Where field labels are placed relative to '
            'inputs: `top` or `left`.'
        ),
    )
    layout = DocChoiceField(
        read_only=True,
        choices=FieldSetLayout.CHOICES,
        example=FieldSetLayout.VERTICAL,
        help_text=(
            'How fields are arranged: `vertical` or '
            '`horizontal`.'
        ),
    )
    fields = TaskFieldEventSerializer(
        many=True,
        help_text='Fields snapshot at the time of the event.',
    )
