from typing import Dict, Any, List
from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    CharField,
)
from pneumatic_backend.processes.models import FieldTemplate
from pneumatic_backend.processes.api_v2.serializers.template.selection import (
    FieldTemplateSelectionSerializer,
    FieldTemplateSelectionListSerializer
)
from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationApiNameMixin,
)
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0005,
    MSG_PT_0006,
    MSG_PT_0050,
)


class PublicFieldTemplateSerializer(ModelSerializer):

    class Meta:
        model = FieldTemplate
        fields = (
            'type',
            'name',
            'description',
            'is_required',
            'selections',
            'order',
            'api_name',
            'default',
        )

    order = IntegerField()
    api_name = CharField(required=False, max_length=200)
    selections = FieldTemplateSelectionSerializer(
        many=True,
        required=False
    )


class FieldTemplateSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationApiNameMixin,
    ModelSerializer
):

    class Meta:
        model = FieldTemplate
        api_primary_field = 'api_name'
        fields = (
            'type',
            'name',
            'description',
            'is_required',
            'selections',
            'order',
            'api_name',
            'default',
        )
        create_or_update_fields = {
            'type',
            'name',
            'description',
            'is_required',
            'order',
            'default',
            'api_name',
            'kickoff',
            'task',
            'template',
        }

    order = IntegerField()
    api_name = CharField(required=False, max_length=200)
    selections = FieldTemplateSelectionSerializer(
        many=True,
        required=False
    )

    def additional_validate_selections(
        self,
        value: List[Dict[str, Any]],
        data: Dict[str, Any]
    ):

        # TODO Need API test
        selection_not_provided = (
            data['type'] in FieldType.TYPES_WITH_SELECTIONS
            and not value
        )
        if selection_not_provided:
            self.raise_validation_error(
                message=MSG_PT_0005,
                api_name=data.get('api_name')
            )

    def additional_validate_type(self, value: str, data: Dict[str, Any]):

        if value == FieldType.USER:
            required = data.get('is_required')
            if not required:
                self.raise_validation_error(
                    message=MSG_PT_0006,
                    api_name=data.get('api_name')
                )

    def to_representation(self, data: Dict[str, Any]):
        data = super().to_representation(data)
        if data.get('description') is None:
            data['description'] = ''
        if data['type'] not in FieldType.TYPES_WITH_SELECTIONS:
            data.pop('selections', None)
        return data

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        step = 'Kickoff' if kickoff else f'Step "{task.name}"'
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'kickoff': kickoff,
                'task': task,
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0050(
                step_name=step,
                name=validated_data.get("name"),
                api_name=validated_data.get('api_name'),
            )
        )
        self.create_or_update_related(
            data=validated_data.get('selections'),
            ancestors_data={
                'field_template': instance,
                'template': self.context['template']
            },
            slz_cls=FieldTemplateSelectionSerializer,
            slz_context={
                'field_template': instance,
                **self.context
            }
        )
        return instance

    def update(
        self,
        instance: FieldTemplate,
        validated_data: Dict[str, Any]
    ):
        self.additional_validate(validated_data)
        task = self.context.get('task')
        kickoff = self.context.get('kickoff')
        step = 'Kickoff' if kickoff else f'Step "{task.name}"'
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'kickoff': kickoff,
                'task': task,
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0050(
                step_name=step,
                name=validated_data.get("name"),
                api_name=validated_data.get('api_name'),
            )
        )
        self.create_or_update_related(
            data=validated_data.get('selections'),
            ancestors_data={
                'field_template': instance,
                'template': self.context['template']
            },
            slz_cls=FieldTemplateSelectionSerializer,
            slz_context={
                'field_template': instance,
                **self.context
            },
        )
        return instance


class FieldTemplateShortViewSerializer(ModelSerializer):
    class Meta:
        model = FieldTemplate
        fields = (
            'type',
            'name',
            'api_name',
        )


class FieldTemplateListSerializer(ModelSerializer):

    class Meta:
        model = FieldTemplate
        fields = (
            'name',
            'type',
            'is_required',
            'description',
            'api_name',
            'selections',
            'order',
        )

    selections = FieldTemplateSelectionListSerializer(many=True)
