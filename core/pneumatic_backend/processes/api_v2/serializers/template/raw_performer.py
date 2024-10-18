from typing import Dict, Any
from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    Serializer,
    IntegerField,
    CharField,
    ChoiceField,
)

from pneumatic_backend.processes.models import (
    FieldTemplate,
    RawPerformerTemplate
)

from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    AdditionalValidationMixin
)
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0032,
    MSG_PT_0033,
    MSG_PT_0034,
    MSG_PT_0035,
    MSG_PT_0036,
    MSG_PT_0056
)
from pneumatic_backend.processes.enums import PerformerType
from pneumatic_backend.processes.api_v2.serializers.template.mixins import (
    CreateOrUpdateInstanceMixin
)

UserModel = get_user_model()


class RawPerformerSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    Serializer
):

    class Meta:
        model = RawPerformerTemplate
        api_primary_field = 'api_name'
        fields = (
            'id',
            'source_id',
            'type',
            'label',
            'api_name'
        )
        create_or_update_fields = {
            'field',
            'template',
            'account',
            'task',
            'source_id',
            'type',
            'label',
            'api_name',
            'user_id',
        }

    id = IntegerField(required=False)
    api_name = CharField(max_length=200, required=False)
    source_id = CharField(allow_null=True)
    type = ChoiceField(choices=PerformerType.choices)
    label = CharField(required=False)

    def additional_validate_raw_performers_type_field(
        self,
        data: Dict[str, Any]
    ):

        task = self.context['task']
        available_api_names = self.context.get(
            'prev_tasks_fields_api_names'
        ) or task.get_prev_tasks_fields_api_names()
        api_name = data.get('source_id')
        if not api_name:
            self.raise_validation_error(
                message=MSG_PT_0036,
                api_name=task.api_name
            )
        if api_name not in available_api_names:
            self.raise_validation_error(
                message=MSG_PT_0034,
                api_name=task.api_name
            )

    def additional_validate_raw_performers_type_user(
        self,
        data: Dict[str, Any]
    ):

        all_user_ids = []
        account = self.context['account']
        task = self.context['task']

        user_id = data.get('source_id')
        if not user_id:
            self.raise_validation_error(
                message=MSG_PT_0032,
                api_name=task.api_name
            )
        try:
            all_user_ids.append(int(user_id))
        except (ValueError, TypeError):
            self.raise_validation_error(
                message=MSG_PT_0033,
                api_name=task.api_name
            )

        unique_user_ids = set(all_user_ids)
        account_user_ids = (
            self.context.get('account_user_ids') or
            account.get_user_ids(include_invited=True)
        )
        undefined_ids = unique_user_ids - account_user_ids
        if undefined_ids:
            self.raise_validation_error(
                message=MSG_PT_0034,
                api_name=task.api_name
            )

    def additional_validate_raw_performers_type_workflow_starter(
        self,
        data: Dict[str, Any]
    ):
        task = self.context['task']
        template = task.template
        if template.is_public or template.is_embedded:
            self.raise_validation_error(
                message=MSG_PT_0035,
                api_name=task.api_name
            )

    def additional_validate(
        self,
        data: Dict[str, Any]
    ):
        super().additional_validate(data)
        performer_type: PerformerType = data['type']
        validate_method_name = (
            f'additional_validate_raw_performers_type_{performer_type}'
        )
        validate_method = getattr(self, validate_method_name, None)
        if validate_method:
            validate_method(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, RawPerformerTemplate):
            if instance.type == PerformerType.USER:
                data['source_id'] = str(instance.user_id)
                data['label'] = instance.user.name_by_status
            elif instance.type == PerformerType.FIELD:
                data['source_id'] = instance.field.api_name
                data['label'] = instance.field.name
            elif instance.type == PerformerType.WORKFLOW_STARTER:
                data['source_id'] = None
                data['label'] = 'Workflow starter'
            data['id'] = instance.id
        return data

    def create(self, validated_data):
        self.additional_validate(validated_data)
        raw_performer_data = {
            'account': self.context['account'],
            'template': self.context['template'],
            'task': self.context['task'],
            'type': validated_data['type'],
        }
        if validated_data.get('api_name'):
            raw_performer_data['api_name'] = validated_data['api_name']
        if validated_data['type'] == PerformerType.USER:
            raw_performer_data['user_id'] = validated_data['source_id']
        elif validated_data['type'] == PerformerType.FIELD:
            api_name = validated_data['source_id']
            field = FieldTemplate.objects.get(
                template=self.context['template'],
                api_name=api_name
            )
            raw_performer_data['field'] = field
        return self.create_or_update_instance(
            validated_data=raw_performer_data,
            not_unique_exception_msg=MSG_PT_0056(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )

    def update(self, instance, validated_data):
        self.additional_validate(validated_data)
        raw_performer_data = {
            'account': self.context['account'],
            'template': self.context['template'],
            'task': self.context['task'],
            'type': validated_data['type']
        }
        if validated_data.get('api_name'):
            raw_performer_data['api_name'] = validated_data['api_name']
        if validated_data['type'] == PerformerType.USER:
            raw_performer_data['user_id'] = validated_data['source_id']
        elif validated_data['type'] == PerformerType.FIELD:
            api_name = validated_data['source_id']
            field = FieldTemplate.objects.get(
                template=self.context['template'],
                api_name=api_name
            )
            raw_performer_data['field'] = field
        return self.create_or_update_instance(
            instance=instance,
            validated_data=raw_performer_data,
            not_unique_exception_msg=MSG_PT_0056(
                step_name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            )
        )
