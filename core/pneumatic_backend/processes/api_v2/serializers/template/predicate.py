# pylint: disable=raising-bad-type
from typing import Dict, Any, Optional

from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin,
    CustomValidationApiNameMixin
)
from pneumatic_backend.processes.models import (
    PredicateTemplate,
    FieldTemplateSelection,
)
from pneumatic_backend.processes.enums import (
    FieldType,
    PredicateOperator
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0043,
    MSG_PT_0044,
    MSG_PT_0045,
    MSG_PT_0046,
    MSG_PT_0051,
)


class PredicateTemplateSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    CreateOrUpdateInstanceMixin,
    ModelSerializer
):
    class Meta:
        model = PredicateTemplate
        api_primary_field = 'api_name'
        fields = (
            'operator',
            'field_type',
            'field',
            'value',
            'api_name',
        )
        create_or_update_fields = {
            'operator',
            'field_type',
            'field',
            'value',
            'api_name',
            'rule',
            'template',
        }

    api_name = CharField(max_length=200, required=False)

    def _validate_allowed_operators(
        self,
        operator: PredicateOperator,
        field_type: FieldType,
        predicate_api_name: Optional[str] = None
    ):
        if operator not in PredicateOperator.ALLOWED_OPERATORS[field_type]:
            raise raise_validation_error(
                message=MSG_PT_0044(
                    field_type=field_type,
                    operator=operator,
                    task=self.context['task'].name,
                ),
                api_name=predicate_api_name
            )

    def _validate_value(
        self,
        value: str,
        operator: PredicateOperator,
        predicate_api_name: Optional[str] = None,
    ) -> str:
        if value is None and operator in PredicateOperator.UNARY_OPERATORS:
            return value

        elif value is None:
            raise raise_validation_error(
                message=MSG_PT_0046(
                    task=self.context['task'].name,
                    operator=operator,
                ),
                api_name=predicate_api_name
            )

        return value

    def _validate_user(
        self,
        account,
        user_id: str,
        predicate_api_name: Optional[str] = None,
    ):
        task_name = self.context['task'].name
        try:
            user_id = int(user_id)
            if not account.users.filter(id=user_id).exists():
                raise_validation_error(
                    message=MSG_PT_0043(user_id=user_id, task=task_name),
                    api_name=predicate_api_name
                )
        except ValueError:
            raise_validation_error(
                message=MSG_PT_0043(user_id=user_id, task=task_name),
                api_name=predicate_api_name
            )
        return user_id

    def _validate_selection(
        self,
        field_api_name: str,
        selection_api_name: str,
        predicate_api_name: Optional[str] = None,
    ):
        if not FieldTemplateSelection.objects.filter(
            api_name=selection_api_name,
            field_template__api_name=field_api_name,
        ).exists():
            raise_validation_error(
                message=MSG_PT_0045(
                    task=self.context['task'].name,
                    selection_api_name=selection_api_name
                ),
                api_name=predicate_api_name
            )
        return selection_api_name

    def additional_validate(self, data: Dict[str, Any]):
        super().additional_validate(data)
        account = self.context['account']
        field_type = data['field_type']
        operator = data['operator']
        value = data.get('value')
        field = data['field']
        api_name = data.get('api_name')

        self._validate_allowed_operators(
            operator=operator,
            field_type=field_type,
            predicate_api_name=api_name
        )
        if self._validate_value(
            operator=operator,
            value=value,
            predicate_api_name=api_name
        ) is not None:
            if field_type == FieldType.USER:
                self._validate_user(
                    account=account,
                    user_id=value,
                    predicate_api_name=api_name
                )

            if field_type in FieldType.TYPES_WITH_SELECTIONS:
                self._validate_selection(
                    field_api_name=field,
                    selection_api_name=value,
                    predicate_api_name=api_name
                )

    def create(self, validated_data):
        self.additional_validate(validated_data)
        return self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'rule':  self.context.get('rule'),
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0051(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )

    def update(self, instance, validated_data):
        self.additional_validate(validated_data)
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'rule':  self.context.get('rule'),
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0051(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )
