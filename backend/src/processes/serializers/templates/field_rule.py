from typing import Any, Dict

from rest_framework.serializers import ModelSerializer, ValidationError

from src.generics.fields import (
    DocCharField,
    DocChoiceField,
    DocIntegerField,
)
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.enums import FieldRuleOperator, FieldRuleType
from src.processes.messages.template import (
    MSG_PT_0075,
    MSG_PT_0079,
)
from src.processes.models.templates.fields import (
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationApiNameMixin,
)


class FieldTemplateRuleGroupAndSerializer(
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateRuleGroupAnd
        api_primary_field = 'api_name'
        fields = (
            'api_name',
            'field',
            'operator',
            'value',
        )
        create_or_update_fields = {
            'api_name',
            'field',
            'operator',
            'value',
            'group_or',
            'template',
            'account',
        }

    api_name = DocCharField(
        max_length=200,
        required=False,
        example='field-rule-group-and-1',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    field = DocCharField(
        max_length=200,
        example='field-1',
        help_text=(
            '`api_name` of the source field this condition reads. '
            'Required for a type "show".'
        ),
        required=False,
        allow_null=True,
    )
    operator = DocChoiceField(
        choices=FieldRuleOperator.CHOICES,
        example=FieldRuleOperator.EQUAL,
        help_text=(
            'Comparison against `value`. Allowed operators '
            'depend on the source field type.'
        ),
    )
    value = DocCharField(
        max_length=200,
        required=False,
        allow_null=True,
        allow_blank=True,
        example='yes',
        help_text=(
            'Value the source field is compared against.'
        ),
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        ruleset_type = (
            self.context['ruleset'].type
            if self.context.get('ruleset')
            else self.context['ruleset_type']
        )
        if ruleset_type == FieldRuleType.SHOW and not attrs.get('field'):
            raise ValidationError(MSG_PT_0079)
        return attrs

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        field = self.context['field']
        task_name = 'Kickoff' if kickoff else task.name
        return self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'group_or': self.context['group_or'],
                'field': field,
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0075(
                task_name=task_name,
                field_name=field.name,
                api_name=validated_data.get('api_name'),
            ),
        )

    def update(
        self,
        instance: FieldTemplateRuleGroupAnd,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        field = self.context['field']
        task_name = 'Kickoff' if kickoff else task.name
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'group_or': self.context['group_or'],
                'field': field,
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0075(
                task_name=task_name,
                field_name=field.name,
                api_name=validated_data.get('api_name'),
            ),
        )


class FieldTemplateRuleGroupOrSerializer(
    CreateOrUpdateRelatedMixin,
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateRuleGroupOr
        api_primary_field = 'api_name'
        fields = (
            'api_name',
            'groups_and',
        )
        create_or_update_fields = {
            'api_name',
            'ruleset',
            'template',
            'account',
        }

    api_name = DocCharField(
        max_length=200,
        required=False,
        example='field-rule-group-or-1',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    groups_and = FieldTemplateRuleGroupAndSerializer(
        many=True,
        help_text=(
            'AND conditions inside this OR branch. '
            'All must be true for the branch to pass.'
        ),
    )

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        field = self.context['field']
        task_name = 'Kickoff' if kickoff else task.name
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'ruleset': self.context['ruleset'],
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0075(
                task_name=task_name,
                field_name=field.name,
                api_name=validated_data.get('api_name'),
            ),
        )
        self.create_or_update_related(
            data=validated_data.pop('groups_and', None),
            slz_cls=FieldTemplateRuleGroupAndSerializer,
            ancestors_data={
                'group_or': instance,
                'template': self.context['template'],
            },
            slz_context={
                'group_or': instance,
                **self.context,
            },
        )
        return instance

    def update(
        self,
        instance: FieldTemplateRuleGroupOr,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        field = self.context['field']
        task_name = 'Kickoff' if kickoff else task.name
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'ruleset': self.context['ruleset'],
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0075(
                task_name=task_name,
                field_name=field.name,
                api_name=validated_data.get('api_name'),
            ),
        )
        self.create_or_update_related(
            data=validated_data.pop('groups_and', None),
            slz_cls=FieldTemplateRuleGroupAndSerializer,
            ancestors_data={
                'group_or': instance,
                'template': self.context['template'],
            },
            slz_context={
                'group_or': instance,
                **self.context,
            },
        )
        return instance


class FieldTemplateRuleSetSerializer(
    CreateOrUpdateRelatedMixin,
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateRuleSet
        api_primary_field = 'api_name'
        fields = (
            'api_name',
            'name',
            'type',
            'message',
            'order',
            'groups_or',
        )
        create_or_update_fields = {
            'api_name',
            'name',
            'type',
            'message',
            'order',
            'field',
            'template',
            'account',
        }

    api_name = DocCharField(
        max_length=200,
        required=False,
        example='ruleset-1',
        help_text='Stable unique identifier. Generated if omitted.',
    )
    name = DocCharField(
        max_length=200,
        example='Show when value is yes',
        help_text='The ruleset name displayed in the editor.',
    )
    type = DocChoiceField(
        choices=FieldRuleType.CHOICES,
        example=FieldRuleType.SHOW,
        help_text=(
            '`show` — reveal this field when conditions '
            'are true. `validator` — treat the value as '
            'valid when conditions are true.'
        ),
    )
    message = DocCharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        example='Amount must be greater than 0',
        help_text=(
            'Error shown when a `validator` ruleset '
            'fails. Unused for `show`.'
        ),
    )
    order = DocIntegerField(
        required=False,
        default=0,
        min_value=0,
        example=0,
        help_text=(
            'Evaluation order among this field\'s '
            'rulesets. Starts at 0.'
        ),
    )
    groups_or = FieldTemplateRuleGroupOrSerializer(
        many=True,
        help_text=(
            'OR branches. The ruleset passes if any '
            'branch is true.'
        ),
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            self.context['ruleset_type'] = data.get('type')
        return super().to_internal_value(data)

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        field = self.context['field']
        task_name = 'Kickoff' if kickoff else task.name
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'field': field,
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0075(
                task_name=task_name,
                field_name=field.name,
                api_name=validated_data.get('api_name'),
            ),
        )
        self.create_or_update_related(
            data=validated_data.get('groups_or'),
            slz_cls=FieldTemplateRuleGroupOrSerializer,
            ancestors_data={
                'ruleset': instance,
                'template': self.context['template'],
            },
            slz_context={
                'ruleset': instance,
                **self.context,
            },
        )
        return instance

    def update(
        self,
        instance: FieldTemplateRuleSet,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        field = self.context['field']
        task_name = 'Kickoff' if kickoff else task.name
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'field': field,
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0075(
                task_name=task_name,
                field_name=field.name,
                api_name=validated_data.get('api_name'),
            ),
        )
        self.create_or_update_related(
            data=validated_data.get('groups_or'),
            slz_cls=FieldTemplateRuleGroupOrSerializer,
            ancestors_data={
                'ruleset': instance,
                'template': self.context['template'],
            },
            slz_context={
                'ruleset': instance,
                **self.context,
            },
        )
        return instance
