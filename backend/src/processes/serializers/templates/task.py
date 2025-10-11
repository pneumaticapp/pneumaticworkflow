# ruff: noqa: PLC0415
from typing import Dict, Any, List, Optional
from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    ModelSerializer,
    IntegerField,
    CharField,
    Serializer,
    BooleanField,
    ReadOnlyField,
)

from src.processes.serializers.templates.condition import (
    ConditionTemplateSerializer,
)
from src.processes.models import (
    TaskTemplate,
    FieldTemplate,
)
from src.processes.serializers.templates.checklist import (
    ChecklistTemplateSerializer,
)
from src.processes.serializers.templates.raw_due_date import (
    RawDueDateTemplateSerializer,
)
from src.processes.serializers.templates.field import (
    FieldTemplateSerializer,
    FieldTemplateShortViewSerializer,
)
from src.generics.mixins.serializers import (
    AdditionalValidationMixin,
    CustomValidationErrorMixin,
)
from src.processes.serializers.templates.raw_performer import (
    RawPerformerSerializer,
)
from src.processes.serializers.templates.mixins import (
    CreateOrUpdateRelatedMixin,
    CreateOrUpdateInstanceMixin,
    CustomValidationApiNameMixin,
)
from src.processes.utils.common import (
    VAR_PATTERN, create_api_name,
)
from src.processes.enums import (
    PerformerType,
    PredicateType,
)
from src.analytics.services import AnalyticService
from src.processes.messages import template as messages


UserModel = get_user_model()


class TaskTemplateSerializer(
    CreateOrUpdateRelatedMixin,
    CreateOrUpdateInstanceMixin,
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    CustomValidationApiNameMixin,
    ModelSerializer,
):

    class Meta:
        model = TaskTemplate
        api_primary_field = 'api_name'
        fields = (
            'id',
            'name',
            'number',
            'description',
            'require_completion_by_all',
            'delay',
            'fields',
            'conditions',
            'api_name',
            'raw_performers',
            'checklists',
            'raw_due_date',
            'revert_task',
            'parents',
            'ancestors',
        )
        create_or_update_fields = {
            'name',
            'number',
            'description',
            'require_completion_by_all',
            'delay',
            'api_name',
            'template',
            'account',
            'revert_task',
            'parents',
            'ancestors',
        }

    number = IntegerField()
    api_name = CharField(max_length=200, required=False)
    fields = FieldTemplateSerializer(many=True, required=False)
    checklists = ChecklistTemplateSerializer(many=True, required=False)
    conditions = ConditionTemplateSerializer(many=True, required=False)
    raw_performers = RawPerformerSerializer(
        many=True,
        required=False,
    )
    raw_due_date = RawDueDateTemplateSerializer(
        required=False,
        allow_null=True,
    )
    parents = ReadOnlyField()
    ancestors = ReadOnlyField()

    def validate(self, data):
        if not data.get('api_name'):
            data['api_name'] = create_api_name(
                prefix=TaskTemplate.api_name_prefix,
            )
        return data

    def get_raw_performers_ctx(
        self,
        task_template: TaskTemplate,
        raw_performers_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        context = {
            **self.context,
            'task': task_template,
        }
        if not raw_performers_data:
            return context
        performers_types = {
            elem.get('type')
            for elem in raw_performers_data
        }
        if PerformerType.FIELD in performers_types:
            context['available_api_names'] = (
                task_template.get_prev_tasks_fields_api_names()
            )
        if PerformerType.USER in performers_types:
            context['account_user_ids'] = set(
                self.context['account'].get_user_ids(include_invited=True),
            )
        return context

    def _get_task_available_fields(
        self,
    ) -> List[FieldTemplate]:

        if getattr(self, '_task_available_fields', None) is None:
            template = self.context['template']
            self._task_available_fields = list(template.get_fields())
        return self._task_available_fields

    def additional_validate_name(
        self,
        value: str,
        data: Dict[str, Any],
        **kwargs,
    ):

        """ Checks three cases:
            1. If api-name is in task name, this field is available
            (created in previous steps).
            2. If only api-names is in task name, at least one field
            must be required. """

        api_names_in_name = {
            api_name.strip()
            for api_name in VAR_PATTERN.findall(value)
        }
        if not api_names_in_name:
            return

        available_fields = self._get_task_available_fields()
        available_api_names = {field.api_name for field in available_fields}
        failed_api_names = api_names_in_name - available_api_names
        if failed_api_names:
            self.raise_validation_error(
                message=messages.MSG_PT_0038(data['name']),
                api_name=data.get('api_name'),
            )

        contains_only_api_names = VAR_PATTERN.sub('', value).strip() == ''
        if contains_only_api_names:
            not_required_fields = True
            for field in available_fields:
                if field.api_name in api_names_in_name and field.is_required:
                    not_required_fields = False
                    break
            if not_required_fields:
                self.raise_validation_error(
                    message=messages.MSG_PT_0039(data['number']),
                    api_name=data.get('api_name'),
                )

    def additional_validate_description(
        self,
        value: Optional[str],
        data: Dict[str, Any],
    ):

        """ Checks that api-name in text should be available
             (created in previous steps) """

        if not value:
            return

        api_names_in_description = {
            api_name.strip()
            for api_name in VAR_PATTERN.findall(value)
        }
        if not api_names_in_description:
            return True

        available_api_names_for_description = {
            field.api_name for field in self._get_task_available_fields()
        }

        failed_api_names_exist = (
            api_names_in_description - available_api_names_for_description
        )
        if failed_api_names_exist:
            self.raise_validation_error(
                message=messages.MSG_PT_0037(data['number']),
                api_name=data.get('api_name'),
            )

    def additional_validate_raw_performers(
        self,
        value: List[Dict[str, str]],
        data: Dict[str, Any],
    ):

        if not value:
            self.raise_validation_error(
                message=messages.MSG_PT_0002,
                api_name=data.get('api_name'),
            )

        unique_performers = {
            (elem.get('type'), elem.get('source_id'))
            for elem in value
        }
        if len(value) != len(unique_performers):
            self.raise_validation_error(
                message=messages.MSG_PT_0003,
                api_name=data.get('api_name'),
            )

    def additional_validate_conditions(
        self,
        value: Optional[List[Dict[str, Any]]],
        data: Dict[str, Any],
    ):

        if isinstance(value, list):
            # TODO move validation to PredicateTemplateSerializer
            #  add task api_names validation
            #  https://my.pneumatic.app/workflows/35698/
            api_names_in_conditions = {
                predicate['field']
                for condition in value
                for rule in condition['rules']
                for predicate in rule['predicates']
                if predicate['field_type'] in PredicateType.FIELD_TYPES
            }
            available_api_names_for_conditions = {
                field.api_name
                for field in self._get_task_available_fields()
            }

            failed_api_names_exist = (
                api_names_in_conditions - available_api_names_for_conditions
            )
            if failed_api_names_exist:
                self.raise_validation_error(
                    message=messages.MSG_PT_0004(data.get('name')),
                    api_name=data.get('api_name'),
                )

    def additional_validate_revert_task(
        self,
        value: Optional[str],
        data: Dict[str, Any],
    ):
        if value:
            api_name = data.get('api_name')
            if api_name:
                if api_name == value:
                    self.raise_validation_error(
                        message=messages.MSG_PT_0060(data.get('name')),
                        api_name=api_name,
                    )
                ancestors = self.context['ancestors_by_tasks'][api_name]
                if value not in ancestors:
                    self.raise_validation_error(
                        message=messages.MSG_PT_0061(data.get('name')),
                        api_name=api_name,
                    )

    def create_or_update_instance(
        self,
        validated_data: Dict[str, Any],
        instance: Optional[TaskTemplate] = None,
    ) -> TaskTemplate:

        if not validated_data.get('delay'):
            validated_data['delay'] = None
        instance = super().create_or_update_instance(
            validated_data=validated_data,
            instance=instance,
            not_unique_exception_msg=messages.MSG_PT_0055(
                name=validated_data.get('name'),
                api_name=validated_data.get('api_name'),
            ),
        )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('description') is None:
            data['description'] = ''
        if data.get('fields') is None:
            data['fields'] = []
        if data.get('raw_performers') is None:
            data['raw_performers'] = []
        if data.get('conditions') is None:
            data['conditions'] = []
        if not data['delay']:
            data['delay'] = None
        return data

    def _remove_notexistent_checklist_items(
        self,
        template,
        task,
        data: Optional[List[Dict[str, Any]]] = None,
    ):

        # TODO Remove in https://my.pneumatic.app/workflows/18128
        if not data:
            return
        from src.processes.models import (
            ChecklistTemplateSelection,
        )
        pairs = {}
        for checklist_data in data:
            for s in checklist_data['selections']:
                pairs[s.get('api_name')] = checklist_data.get('api_name')
        for selection in ChecklistTemplateSelection.objects.select_related(
            'checklist',
        ).filter(
            template=template,
            checklist__task=task,
            api_name__in=pairs.keys(),
        ):
            checklist_api_name = pairs.get(selection.api_name)
            if checklist_api_name:
                if selection.checklist.api_name != checklist_api_name:
                    selection.delete()

    def create(self, validated_data: Dict[str, Any]):
        self.additional_validate(validated_data)
        api_name = validated_data['api_name']
        parents = self.context['parents_by_tasks'][api_name]
        ancestors = list(self.context['ancestors_by_tasks'][api_name])
        instance = self.create_or_update_instance(
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'parents': parents,
                'ancestors': ancestors,
                **validated_data,
            },
        )
        template = self.context['template']
        if template.is_active and validated_data.get('raw_due_date'):
            AnalyticService.templates_task_due_date_created(
                user=self.context['user'],
                template=template,
                task=instance,
                is_superuser=self.context['is_superuser'],
                auth_type=self.context['auth_type'],
            )

        self.create_or_update_related(
            data=validated_data.get('fields'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=FieldTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
            },
        )

        raw_performers_data = validated_data.get('raw_performers')
        raw_performers_clz_context = self.get_raw_performers_ctx(
            task_template=instance,
            raw_performers_data=raw_performers_data,
        )
        self.create_or_update_related(
            data=raw_performers_data,
            ancestors_data={
                'task': instance,
            },
            slz_cls=RawPerformerSerializer,
            slz_context=raw_performers_clz_context,
        )

        self.create_or_update_related(
            data=validated_data.get('conditions'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=ConditionTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
                'ancestors': ancestors,
            },
        )

        # TODO tmp crutch
        self._remove_notexistent_checklist_items(
            template=self.context['template'],
            task=instance,
            data=validated_data.get('checklists'),
        )

        self.create_or_update_related(
            data=validated_data.get('checklists'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=ChecklistTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
            },
        )

        self.create_or_update_related_one(
            data=validated_data.get('raw_due_date'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=RawDueDateTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
            },
        )
        return instance

    def update(
        self,
        instance: TaskTemplate,
        validated_data: Dict[str, Any],
    ):
        self.additional_validate(validated_data)
        api_name = validated_data['api_name']
        parents = self.context['parents_by_tasks'][api_name]
        ancestors = list(self.context['ancestors_by_tasks'][api_name])
        template = self.context['template']
        raw_due_date_created = (
            template.is_active
            and not hasattr(self.instance, 'raw_due_date')
            and validated_data.get('raw_due_date')
        )
        instance = self.create_or_update_instance(
            instance=instance,
            validated_data={
                'template': self.context['template'],
                'account': self.context['account'],
                'parents': parents,
                'ancestors': ancestors,
                **validated_data,
            },
        )
        if raw_due_date_created:
            AnalyticService.templates_task_due_date_created(
                user=self.context['user'],
                template=template,
                task=instance,
                is_superuser=self.context['is_superuser'],
                auth_type=self.context['auth_type'],
            )
        self.create_or_update_related(
            data=validated_data.get('fields'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=FieldTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
            },
        )

        raw_performers_data = validated_data.get('raw_performers')
        raw_performers_clz_context = self.get_raw_performers_ctx(
            task_template=instance,
            raw_performers_data=raw_performers_data,
        )
        self.create_or_update_related(
            data=raw_performers_data,
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=RawPerformerSerializer,
            slz_context=raw_performers_clz_context,
        )

        self.create_or_update_related(
            data=validated_data.get('conditions'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=ConditionTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
                'ancestors': ancestors,
            },
        )
        # TODO tmp crutch
        self._remove_notexistent_checklist_items(
            template=self.context['template'],
            task=instance,
            data=validated_data.get('checklists'),
        )

        self.create_or_update_related(
            data=validated_data.get('checklists'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=ChecklistTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
            },
        )

        self.create_or_update_related_one(
            data=validated_data.get('raw_due_date'),
            ancestors_data={
                'task': instance,
                'template': self.context['template'],
            },
            slz_cls=RawDueDateTemplateSerializer,
            slz_context={
                **self.context,
                'task': instance,
            },
        )
        return instance


class TemplateStepNameSerializer(ModelSerializer):
    class Meta:
        model = TaskTemplate
        fields = (
            'id',  # Deprecated
            'name',
            'number',
            'api_name',
        )


class TemplateTaskOnlyFieldsSerializer(ModelSerializer):
    class Meta:
        model = TaskTemplate
        fields = (
            'id',  # Deprecated
            'name',
            'number',
            'api_name',
            'fields',
        )

    fields = FieldTemplateShortViewSerializer(
        many=True,
        required=False,
        read_only=True,
    )


class TaskTemplatePrivilegesSerializer(ModelSerializer):
    class Meta:
        model = TaskTemplate
        fields = (
            'number',
            'api_name',
            'name',
            'raw_performers',
        )

    raw_performers = RawPerformerSerializer(many=True)


class TemplateStepFilterSerializer(
    CustomValidationErrorMixin,
    Serializer,
):

    with_tasks_in_progress = BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )


class ShortTaskSerializer(
    CustomValidationApiNameMixin,
    Serializer,
):
    number = IntegerField(
        min_value=1,
        required=True,
        allow_null=False,
    )
    name = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )
    description = CharField(
        required=True,
        allow_null=False,
        allow_blank=False,
    )

    def validate_name(self, value):
        return value[:TaskTemplate.NAME_MAX_LENGTH]

    def validate_description(self, value):
        return value[:500]
