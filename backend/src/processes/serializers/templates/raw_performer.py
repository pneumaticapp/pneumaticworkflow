from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    Serializer,
)

from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.enums import PerformerType
from src.processes.messages.template import (
    MSG_PT_0032,
    MSG_PT_0033,
    MSG_PT_0034,
    MSG_PT_0035,
    MSG_PT_0036,
    MSG_PT_0056,
    MSG_PT_0071,
    MSG_PT_0072,
    MSG_PT_0073,
    MSG_PT_0074,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateInstanceMixin,
)

UserModel = get_user_model()


class RawPerformerSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CreateOrUpdateInstanceMixin,
    Serializer,
):

    class Meta:
        model = RawPerformerTemplate
        api_primary_field = 'api_name'
        fields = (
            'source_id',
            'type',
            'label',
            'api_name',
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
            'group_id',
            'source_task_api_name',
        }

    api_name = CharField(max_length=200, required=False)
    source_id = CharField(allow_null=True)
    type = ChoiceField(choices=PerformerType.choices)
    label = CharField(required=False)

    def additional_validate_raw_performers_type_field(
        self,
        data: Dict[str, Any],
    ):

        task = self.context['task']
        available_api_names = self.context.get(
            'prev_tasks_fields_api_names',
        ) or task.get_prev_tasks_fields_api_names()
        api_name = data.get('source_id')
        if not api_name:
            self.raise_validation_error(
                message=MSG_PT_0036,
                api_name=task.api_name,
            )
        if api_name not in available_api_names:
            self.raise_validation_error(
                message=MSG_PT_0034,
                api_name=task.api_name,
            )

    def additional_validate_raw_performers_type_user(
        self,
        data: Dict[str, Any],
    ):

        account = self.context['account']
        task = self.context['task']
        user_id = data.get('source_id')
        if not user_id:
            self.raise_validation_error(
                message=MSG_PT_0032,
                api_name=task.api_name,
            )
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            self.raise_validation_error(
                message=MSG_PT_0033,
                api_name=task.api_name,
            )
        account_user_ids = (
            self.context.get('account_user_ids') or
            account.get_user_ids(include_invited=True)
        )
        if user_id not in account_user_ids:
            self.raise_validation_error(
                message=MSG_PT_0034,
                api_name=task.api_name,
            )

    def additional_validate_raw_performers_type_workflow_starter(
        self,
        data: Dict[str, Any],
    ):
        task = self.context['task']
        template = task.template
        if template.is_public or template.is_embedded:
            self.raise_validation_error(
                message=MSG_PT_0035,
                api_name=task.api_name,
            )

    def additional_validate_raw_performers_type_group(
        self,
        data: Dict[str, Any],
    ):
        account = self.context['account']
        task = self.context['task']

        group_id = data.get('source_id')
        if not group_id:
            self.raise_validation_error(
                message=MSG_PT_0032,
                api_name=task.api_name,
            )
        try:
            account.user_groups.get(id=int(group_id))
        except ObjectDoesNotExist:
            self.raise_validation_error(
                message=MSG_PT_0034,
                api_name=task.api_name,
            )
        except (ValueError, TypeError):
            self.raise_validation_error(
                message=MSG_PT_0033,
                api_name=task.api_name,
            )

    def additional_validate_raw_performers_type_manager(
        self,
        data: Dict[str, Any],
    ):
        task = self.context['task']
        source_id = data.get('source_id')
        if not source_id:
            self.raise_validation_error(
                message=MSG_PT_0071,
                api_name=task.api_name,
            )
        elif source_id == task.api_name:
            self.raise_validation_error(
                message=MSG_PT_0072(name=task.name),
                api_name=task.api_name,
            )

        # Cross-step validation via template tasks context
        template_tasks = self.context.get('template_tasks')
        if template_tasks is None:
            return

        source_task_data = template_tasks.get(source_id)
        if not source_task_data:
            self.raise_validation_error(
                message=MSG_PT_0073(
                    name=task.name,
                    step_name=source_id,
                ),
                api_name=task.api_name,
            )
        elif source_task_data.get('require_completion_by_all'):
            self.raise_validation_error(
                message=MSG_PT_0074(
                    name=task.name,
                    step_name=source_task_data.get('name', source_id),
                ),
                api_name=task.api_name,
            )

    def additional_validate(
        self,
        data: Dict[str, Any],
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
            elif instance.type == PerformerType.GROUP:
                data['source_id'] = str(instance.group_id)
                data['label'] = instance.group.name
            elif instance.type == PerformerType.MANAGER:
                source_api_name = instance.source_task_api_name
                data['source_id'] = source_api_name
                template_tasks = self.context.get(
                    'template_tasks',
                )
                if template_tasks is not None:
                    task_data = template_tasks.get(
                        source_api_name, {},
                    )
                    source_task_name = task_data.get('name')
                else:
                    source_task_name = None
                    for task_template in (
                        instance.task.template.tasks.all()
                    ):
                        if task_template.api_name == (
                            source_api_name
                        ):
                            source_task_name = (
                                task_template.name
                            )
                            break
                step_label = (
                    source_task_name or source_api_name
                )
                data['label'] = f'Manager: {step_label}'
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
        elif validated_data['type'] == PerformerType.GROUP:
            raw_performer_data['group_id'] = validated_data['source_id']
        elif validated_data['type'] == PerformerType.FIELD:
            api_name = validated_data['source_id']
            field = FieldTemplate.objects.get(
                template=self.context['template'],
                api_name=api_name,
            )
            raw_performer_data['field'] = field
        elif validated_data['type'] == PerformerType.MANAGER:
            raw_performer_data['source_task_api_name'] = (
                validated_data['source_id']
            )
        return self.create_or_update_instance(
            validated_data=raw_performer_data,
            not_unique_exception_msg=MSG_PT_0056(
                name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            ),
        )

    def update(self, instance, validated_data):
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
        elif validated_data['type'] == PerformerType.GROUP:
            raw_performer_data['group_id'] = validated_data['source_id']
        elif validated_data['type'] == PerformerType.FIELD:
            api_name = validated_data['source_id']
            field = FieldTemplate.objects.get(
                template=self.context['template'],
                api_name=api_name,
            )
            raw_performer_data['field'] = field
        elif validated_data['type'] == PerformerType.MANAGER:
            raw_performer_data['source_task_api_name'] = (
                validated_data['source_id']
            )
        return self.create_or_update_instance(
            instance=instance,
            validated_data=raw_performer_data,
            not_unique_exception_msg=MSG_PT_0056(
                name=self.context['task'].name,
                api_name=validated_data.get('api_name'),
            ),
        )
