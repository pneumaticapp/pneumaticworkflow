from rest_framework import serializers

from src.generics.fields import (
    DocBooleanField,
    DocCharField,
    DocChoiceField,
    DocIntegerField,
)
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
)
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    FieldSelection,
    TaskField,
)


class FieldRuleGroupAndSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldRuleGroupAnd
        fields = (
            'api_name',
            'field',
            'operator',
            'value',
        )

    api_name = DocCharField(
        read_only=True,
        example='field-rule-group-and-1',
        help_text='Stable unique identifier.',
    )
    field = DocCharField(
        read_only=True,
        example='field-1',
        help_text='`api_name` of the source field this condition reads.',
    )
    operator = DocChoiceField(
        read_only=True,
        choices=FieldRuleOperator.CHOICES,
        example=FieldRuleOperator.EQUAL,
        help_text=(
            'Comparison against `value`. Allowed operators '
            'depend on the source field type.'
        ),
    )
    value = DocCharField(
        read_only=True,
        example='yes',
        help_text='Value the source field is compared against.',
    )


class FieldRuleGroupOrSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldRuleGroupOr
        fields = (
            'api_name',
            'groups_and',
        )

    api_name = DocCharField(
        read_only=True,
        example='field-rule-group-or-1',
        help_text='Stable unique identifier.',
    )
    groups_and = FieldRuleGroupAndSerializer(
        many=True,
        read_only=True,
        help_text=(
            'AND conditions inside this OR branch. '
            'All must be true for the branch to pass.'
        ),
    )


class FieldRuleSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = FieldRuleSet
        fields = (
            'api_name',
            'name',
            'type',
            'message',
            'order',
            'groups_or',
        )

    api_name = DocCharField(
        read_only=True,
        example='ruleset-1',
        help_text='Stable unique identifier.',
    )
    name = DocCharField(
        read_only=True,
        example='Show when value is yes',
        help_text='The ruleset name displayed in the editor.',
    )
    type = DocChoiceField(
        read_only=True,
        choices=FieldRuleType.CHOICES,
        example=FieldRuleType.SHOW,
        help_text=(
            '`show` — reveal this field when conditions '
            'are true. `validator` — treat the value as '
            'valid when conditions are true.'
        ),
    )
    message = DocCharField(
        read_only=True,
        example='Amount must be greater than 0',
        help_text=(
            'Error shown when a `validator` ruleset '
            'fails. Unused for `show`.'
        ),
    )
    order = DocIntegerField(
        read_only=True,
        example=0,
        help_text=(
            'Evaluation order among this field\'s '
            'rulesets. Starts at 0.'
        ),
    )
    groups_or = FieldRuleGroupOrSerializer(
        many=True,
        read_only=True,
        help_text=(
            'OR branches. The ruleset passes if any '
            'branch is true.'
        ),
    )


class FieldSelectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldSelection
        fields = (
            'id',
            'value',
            'api_name',
        )

    id = DocIntegerField(
        read_only=True,
        example=101,
        help_text='Selection identifier.',
    )
    value = DocCharField(
        read_only=True,
        example='Option 1',
        help_text='Text shown to the user.',
    )
    api_name = DocCharField(
        read_only=True,
        example='selection-1',
        help_text='Stable unique identifier.',
    )


class TaskFieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'order',
            'type',
            'is_required',
            'is_hidden',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
            'selections',
            'rulesets',
        )

    id = DocIntegerField(
        read_only=True,
        example=101,
        help_text='Field identifier.',
    )
    order = DocIntegerField(
        read_only=True,
        example=0,
        help_text='Position of the field in the form. Starts at 0.',
    )
    type = DocChoiceField(
        read_only=True,
        choices=FieldType.CHOICES,
        example=FieldType.STRING,
        help_text='Field kind, defines how the value is entered.',
    )
    is_required = DocBooleanField(
        read_only=True,
        example=True,
        help_text='The task cannot be completed while the value is empty.',
    )
    is_hidden = DocBooleanField(
        read_only=True,
        example=False,
        help_text=(
            'Recalculated from the `show` rulesets after every change '
            'of the values. True while none of them passes.'
        ),
    )
    description = DocCharField(
        read_only=True,
        example='Amount description',
        help_text='Hint shown under the field.',
    )
    api_name = DocCharField(
        read_only=True,
        example='field-1',
        help_text='Stable unique identifier.',
    )
    name = DocCharField(
        read_only=True,
        example='Amount',
        help_text='Field label.',
    )
    value = DocCharField(
        read_only=True,
        example='100',
        help_text='Raw value as entered by the user.',
    )
    markdown_value = DocCharField(
        read_only=True,
        example='100',
        help_text='Value with markdown markup preserved.',
    )
    clear_value = DocCharField(
        read_only=True,
        example='100',
        help_text='Value with markdown markup stripped.',
    )
    user_id = DocIntegerField(
        read_only=True,
        example=None,
        help_text='Selected user for a field of type `user`.',
    )
    group_id = DocIntegerField(
        read_only=True,
        example=None,
        help_text='Selected group for a field of type `user`.',
    )
    selections = serializers.SerializerMethodField(
        help_text=(
            'Available options for `checkbox`, `radio` and `dropdown`. '
            'Values of the linked dataset are appended.'
        ),
    )
    rulesets = FieldRuleSetSerializer(
        many=True,
        read_only=True,
        help_text=(
            'Show and validator rules of the field. '
            'Empty when the field has no rules.'
        ),
    )

    def get_selections(self, instance: TaskField) -> list:
        if hasattr(instance, 'selections_values'):
            # Prefetched values
            result = [s.value for s in instance.selections_values]
        else:
            # Called for single fields where prefetch is not needed
            result = list(instance.selections.values_list('value', flat=True))
        if instance.dataset_id:
            dataset = instance.dataset
            if hasattr(dataset, 'dataset_values'):
                # Prefetched values
                result.extend([i.value for i in dataset.dataset_values])
            else:
                # Called for single fields where prefetch is not needed
                dataset_values = dataset.items.values_list('value', flat=True)
                result.extend(list(dataset_values))
        return result


class TaskFieldListSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'order',
            'task_id',
            'kickoff_id',
            'type',
            'is_required',
            'is_hidden',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
            'fieldset_id',
        )


class TaskFieldEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskField
        fields = (
            'id',
            'order',
            'type',
            'is_required',
            'is_hidden',
            'description',
            'api_name',
            'name',
            'value',
            'markdown_value',
            'clear_value',
            'user_id',
            'group_id',
        )
