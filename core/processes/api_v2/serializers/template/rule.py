from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from pneumatic_backend.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateRelatedMixin,
    CreateOrUpdateInstanceMixin,
    CustomValidationApiNameMixin,
)
from pneumatic_backend.processes.api_v2.serializers.template.predicate import (
    PredicateTemplateSerializer,
)
from pneumatic_backend.processes.models import RuleTemplate
from pneumatic_backend.processes.messages.template import MSG_PT_0053


class RuleTemplateSerializer(
    CreateOrUpdateRelatedMixin,
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer,
):
    class Meta:
        model = RuleTemplate
        api_primary_field = 'api_name'
        fields = (
            'predicates',
            'api_name',
        )
        create_or_update_fields = {
            'api_name',
            'condition',
            'template',
        }

    api_name = CharField(max_length=200, required=False)
    predicates = PredicateTemplateSerializer(
        many=True,
        allow_empty=False,
    )

    def create(self, validated_data):
        self.additional_validate(validated_data)
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'condition':  self.context.get('condition'),
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0053(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )
        self.create_or_update_related(
            data=validated_data.get('predicates'),
            slz_cls=PredicateTemplateSerializer,
            ancestors_data={
                'rule': instance,
                'template': self.context['template'],
            },
            slz_context={
                'rule': instance,
                **self.context
            }
        )
        return instance

    def update(self, instance, validated_data):
        self.additional_validate(validated_data)
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'condition':  self.context.get('condition'),
                **validated_data
            },
            not_unique_exception_msg=MSG_PT_0053(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )
        self.create_or_update_related(
            data=validated_data.get('predicates'),
            slz_cls=PredicateTemplateSerializer,
            ancestors_data={
                'rule': instance,
                'template': self.context['template'],
            },
            slz_context={
                'rule': instance,
                **self.context
            }
        )

        return instance
