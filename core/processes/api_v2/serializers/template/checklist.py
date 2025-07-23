from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
)
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0040,
    MSG_PT_0047,
)
from pneumatic_backend.processes.models import FieldTemplate
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
)
from pneumatic_backend.processes.models.templates.checklist import (
    ChecklistTemplate
)
from pneumatic_backend.processes.api_v2.serializers.template\
    .checklist_selection import ChecklistTemplateSelectionSerializer
from pneumatic_backend.analytics.services import AnalyticService


class ChecklistTemplateSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    ModelSerializer
):

    class Meta:
        model = ChecklistTemplate
        api_primary_field = 'api_name'
        fields = (
            'api_name',
            'selections',
        )
        create_or_update_fields = {
            'api_name',
            'task',
            'template',
        }

    api_name = CharField(required=False, max_length=200)
    selections = ChecklistTemplateSelectionSerializer(
        many=True,
        required=True
    )

    def additional_validate_selections(self, value, data: Dict[str, Any]):
        if not isinstance(value, list) or not value:
            self.raise_validation_error(
                message=MSG_PT_0040,
                api_name=data.get('api_name', self.context['task'].api_name)
            )

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'task':  self.context['task'],
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0047(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name')
            )
        )
        self.create_or_update_related(
            data=validated_data.get('selections'),
            ancestors_data={
                'checklist': instance,
                'template': self.context['template']
            },
            slz_cls=ChecklistTemplateSelectionSerializer,
            slz_context={
                'checklist': instance,
                **self.context
            }
        )
        AnalyticService.checklist_created(
            user=self.context['user'],
            template=self.context['template'],
            task=self.context['task'],
            is_superuser=self.context['is_superuser'],
            auth_type=self.context['auth_type']
        )
        return instance

    def update(
        self,
        instance: FieldTemplate,
        validated_data: Dict[str, Any]
    ):
        self.additional_validate(validated_data)
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'task':  self.context['task'],
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0047(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name')
            )
        )
        self.create_or_update_related(
            data=validated_data.get('selections'),
            ancestors_data={
                'checklist': instance,
                'template': self.context['template']
            },
            slz_cls=ChecklistTemplateSelectionSerializer,
            slz_context={
                'checklist': instance,
                **self.context
            }
        )
        return instance
