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
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldRuleValueType,
    FieldType,
)
from src.processes.messages.template import (
    MSG_PT_0079,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationApiNameMixin,
    FieldRuleApiNameMixin,
    validate_date_timestamp,
)


class FieldTemplateRuleGroupAndSerializer(
    FieldRuleApiNameMixin,
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
            'value_type',
        )
        create_or_update_fields = {
            'api_name',
            'field',
            'operator',
            'value',
            'value_type',
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
    value_type = DocChoiceField(
        choices=FieldRuleValueType.CHOICES,
        required=False,
        allow_null=True,
        example=FieldRuleValueType.USER,
        help_text=(
            'For a user field: `user` compares `value` with '
            'user_id, `group` compares it with group_id. '
            'Empty keeps the legacy match of either id.'
        ),
    )

    def additional_validate_value(self, value, data: Dict[str, Any]):
        if not value:
            return
        source_api_name = data.get('field')
        if source_api_name:
            template = self.context.get('template')
            if not template:
                return
            source_field = FieldTemplate.objects.filter(
                template=template,
                api_name=source_api_name,
            ).first()
        else:
            source_field = self.context.get('field')
        if source_field and source_field.type == FieldType.DATE:
            validate_date_timestamp(value, data.get('api_name'))

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        return self._save_ruleset_instance(
            validated_data=validated_data,
            extra={'group_or': self.context['group_or']},
        )

    def update(
        self,
        instance: FieldTemplateRuleGroupAnd,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        return self._save_ruleset_instance(
            instance=instance,
            validated_data=validated_data,
            extra={'group_or': self.context['group_or']},
        )


class FieldTemplateRuleGroupOrSerializer(
    FieldRuleApiNameMixin,
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
        instance = self._save_ruleset_instance(
            validated_data=validated_data,
            extra={'ruleset': self.context['ruleset']},
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
        instance = self._save_ruleset_instance(
            instance=instance,
            validated_data=validated_data,
            extra={'ruleset': self.context['ruleset']},
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
    FieldRuleApiNameMixin,
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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get('type') != FieldRuleType.SHOW:
            return attrs
        for group_or in attrs.get('groups_or') or []:
            for group_and in group_or.get('groups_and') or []:
                if not group_and.get('field'):
                    raise ValidationError(MSG_PT_0079)
        return attrs

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        instance = self._save_ruleset_instance(
            validated_data=validated_data,
            extra={'field': self.context['field']},
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
        instance = self._save_ruleset_instance(
            instance=instance,
            validated_data=validated_data,
            extra={'field': self.context['field']},
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
