from typing import Any, Dict

from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)

from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.messages.template import MSG_PT_0048
from src.processes.messages.workflow import (
    MSG_PW_0056,
)
from src.processes.models.templates.checklist import (
    ChecklistTemplateSelection,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
)
from src.utils.validation import raise_validation_error


class ChecklistTemplateSelectionSerializer(
    CreateOrUpdateInstanceMixin,
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
    ModelSerializer,
):

    class Meta:
        model = ChecklistTemplateSelection
        api_primary_field = 'api_name'
        fields = (
            'value',
            'api_name',
        )
        create_or_update_fields = {
            'value',
            'api_name',
            'checklist',
            'template',
        }

    value = CharField()
    api_name = CharField(max_length=200, required=False)

    def additional_validate_value(self, value: str, data: dict):
        if len(value) > 2000:
            raise_validation_error(
                message=MSG_PW_0056,
                api_name=data.get('api_name'),
                name='value',
            )
        return value

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        return self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'checklist':  self.context['checklist'],
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0048(
                name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            ),
        )

    def update(
        self,
        instance: ChecklistTemplateSelection,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'checklist':  self.context['checklist'],
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0048(
                name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            ),
        )
