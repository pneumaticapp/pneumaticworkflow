from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer
from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    CustomValidationApiNameMixin,
)
from pneumatic_backend.processes.api_v2.serializers.template.rule import (
    RuleTemplateSerializer,
)
from pneumatic_backend.processes.messages.template import MSG_PT_0049
from pneumatic_backend.processes.models import ConditionTemplate
from pneumatic_backend.analytics.services import AnalyticService


class ConditionTemplateSerializer(
    CustomValidationErrorMixin,
    CreateOrUpdateInstanceMixin,
    CreateOrUpdateRelatedMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer
):
    class Meta:
        model = ConditionTemplate
        api_primary_field = 'api_name'
        fields = (
            'action',
            'rules',
            'order',
            'api_name',
        )
        create_or_update_fields = {
            'action',
            'order',
            'api_name',
            'task',
            'template',
        }

    api_name = CharField(max_length=200, required=False)
    rules = RuleTemplateSerializer(
        many=True,
        allow_empty=False,
    )

    def create(self, validated_data):
        self.additional_validate(validated_data)
        user = self.context['user']
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'task':  self.context['task'],
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0049(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name')
            )
        )
        self.create_or_update_related(
            data=validated_data.get('rules'),
            slz_cls=RuleTemplateSerializer,
            ancestors_data={
                'condition': instance,
                'template': self.context['template'],
            },
            slz_context={
                'condition': instance,
                **self.context
            }
        )
        template = self.context['template']
        if template.is_active:
            AnalyticService.templates_task_condition_created(
                user=user,
                is_superuser=self.context['is_superuser'],
                auth_type=self.context['auth_type'],
                task=self.context['task'],
                condition=instance,
                template=template
            )
        return instance

    def update(self, instance, validated_data):
        self.additional_validate(validated_data)
        template = self.context['template']
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'task':  self.context['task'],
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0049(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name')
            )
        )
        self.create_or_update_related(
            data=validated_data.get('rules'),
            slz_cls=RuleTemplateSerializer,
            ancestors_data={
                'condition': instance,
                'template': template,
            },
            slz_context={
                'condition': instance,
                **self.context
            }
        )
        return instance
