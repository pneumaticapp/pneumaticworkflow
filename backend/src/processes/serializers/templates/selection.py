from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
)
from src.processes.models import (
    FieldTemplateSelection,
)
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
    CustomValidationApiNameMixin,
)
from src.processes.messages.template import MSG_PT_0054


class FieldTemplateSelectionSerializer(
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer,
):

    class Meta:
        model = FieldTemplateSelection
        api_primary_field = 'api_name'
        fields = (
            'value',
            'api_name',
        )
        create_or_update_fields = {
            'value',
            'api_name',
            'field_template',
            'template',
        }

    value = CharField(max_length=200)
    api_name = CharField(max_length=200, required=False)

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        field_template = self.context['field_template']
        value = validated_data['value']
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        step = 'Kickoff' if kickoff else task.name
        return self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'field_template': field_template,
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0054(
                name=step,
                field_name=field_template.name,
                api_name=validated_data.get('api_name'),
                value=value,
            ),
        )

    def update(
        self,
        instance: FieldTemplateSelection,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        field_template = self.context['field_template']
        value = validated_data['value']
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        step = 'Kickoff' if kickoff else task.name
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'field_template': field_template,
                **validated_data,
            },
            not_unique_exception_msg=MSG_PT_0054(
                name=step,
                field_name=field_template.name,
                api_name=validated_data.get('api_name'),
                value=value,
            ),
        )


class FieldTemplateSelectionListSerializer(ModelSerializer):

    class Meta:
        model = FieldTemplateSelection
        fields = (
            'api_name',
            'value',
        )
