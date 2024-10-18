from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    IntegerField,
)
from pneumatic_backend.processes.models import (
    FieldTemplateSelection
)
from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin,
    CustomValidationApiNameMixin,
)
from pneumatic_backend.processes.messages.template import MSG_PT_0054


class FieldTemplateSelectionSerializer(
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer
):

    class Meta:
        model = FieldTemplateSelection
        api_primary_field = 'api_name'
        fields = (
            'id',  # TODO Remove in https://my.pneumatic.app/workflows/34311/
            'value',
            'api_name',
        )
        create_or_update_fields = {
            'value',
            'api_name',
            'field_template',
            'template',
        }

    id = IntegerField(read_only=True)
    value = CharField(max_length=200)
    api_name = CharField(max_length=200, required=False)

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        field_template = self.context['field_template']
        value = validated_data['value']
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        step = 'Kickoff' if kickoff else f'Step "{task.name}"'
        return self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'field_template': field_template,
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0054(
                step_name=step,
                name=field_template.name,
                api_name=validated_data.get('api_name'),
                value=value
            )
        )

    def update(
        self,
        instance: FieldTemplateSelection,
        validated_data: Dict[str, Any]
    ):
        self.additional_validate(validated_data)
        field_template = self.context['field_template']
        value = validated_data['value']
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        step = 'Kickoff' if kickoff else f'Step "{task.name}"'
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'field_template': field_template,
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0054(
                step_name=step,
                name=field_template.name,
                api_name=validated_data.get('api_name'),
                value=value
            )
        )


class FieldTemplateSelectionListSerializer(ModelSerializer):

    class Meta:
        model = FieldTemplateSelection
        fields = (
            'id',  # TODO Remove in https://my.pneumatic.app/workflows/34311/
            'api_name',
            'value',
        )
