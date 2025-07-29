from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
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
from pneumatic_backend.processes.models import (
    RawDueDateTemplate
)
from pneumatic_backend.processes.enums import (
    FieldType,
    DueDateRule,
)
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0027,
    MSG_PT_0028,
    MSG_PT_0029,
    MSG_PT_0030,
    MSG_PT_0031,
    MSG_PT_0052,
)


class RawDueDateTemplateSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    ModelSerializer
):

    """ Required slz context:
        template - Template instance
        task - TaskTemplate instance
    """

    class Meta:
        model = RawDueDateTemplate
        api_primary_field = 'api_name'
        fields = (
            'api_name',
            'duration',
            'duration_months',
            'rule',
            'source_id',
        )
        create_or_update_fields = {
            'api_name',
            'task',
            'template',
            'duration',
            'duration_months',
            'rule',
            'source_id',
        }

    api_name = CharField(required=False, max_length=200)

    def additional_validate(self, data: Dict[str, Any]):
        super().additional_validate(data)

        task_template = self.context['task']
        rule = data['rule']
        api_name = data.get('api_name')
        if rule in DueDateRule.FIELD_RULES:
            field_api_name = data.get('source_id')
            if not field_api_name:
                self.raise_validation_error(
                    message=MSG_PT_0027,
                    api_name=api_name
                )
            prev_tasks_fields_api_names = set(
                task_template.get_prev_tasks_fields(
                    fields_filter_kwargs={'type': FieldType.DATE}
                ).api_names()
            )
            if field_api_name not in prev_tasks_fields_api_names:
                self.raise_validation_error(
                    message=MSG_PT_0028,
                    api_name=api_name
                )
        elif rule in DueDateRule.TASK_RULES:
            template = self.context['template']
            task_api_name = data.get('source_id')
            if not task_api_name:
                self.raise_validation_error(
                    message=MSG_PT_0029,
                    api_name=api_name
                )
            if rule == DueDateRule.AFTER_TASK_COMPLETED:
                prev_tasks_api_names = set(
                    template.tasks.filter(
                        number__lt=task_template.number
                    ).values_list('api_name', flat=True)
                )
                if task_api_name not in prev_tasks_api_names:
                    self.raise_validation_error(
                        message=MSG_PT_0030,
                        api_name=api_name
                    )
            elif rule == DueDateRule.AFTER_TASK_STARTED:
                tasks_api_names = set(
                    template.tasks.filter(
                        number__lte=task_template.number
                    ).values_list('api_name', flat=True)
                )
                if task_api_name not in tasks_api_names:
                    self.raise_validation_error(
                        message=MSG_PT_0031,
                        api_name=api_name
                    )

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        return self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'task':  self.context['task'],
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0052(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )

    def update(
        self,
        instance: FieldTemplate,
        validated_data: Dict[str, Any]
    ):
        self.additional_validate(validated_data)
        return self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'task':  self.context['task'],
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0052(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )
