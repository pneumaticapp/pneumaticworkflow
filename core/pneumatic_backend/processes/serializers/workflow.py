# pylint: disable=comparison-with-callable
import re
from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from pneumatic_backend.generics.paginations import DefaultPagination
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    AdditionalValidationMixin,
)
from pneumatic_backend.processes.models import (
    Workflow,
    TaskPerformer,
    Task,
    TaskTemplate,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    WorkflowApiStatus,
    WorkflowOrdering, TaskStatus,
)
from pneumatic_backend.processes.paginations import WorkflowListPagination
from pneumatic_backend.processes.serializers.kickoff_value import (
    KickoffValueInfoSerializer,
)
from pneumatic_backend.processes.serializers.template import (
    TemplateDetailsSerializer,
    WorkflowTemplateSerializer,
)
from pneumatic_backend.processes.serializers.field import (
    TaskFieldListSerializer,
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.task import (
    TasksPassedInfoSerializer,
    WorkflowCurrentTaskSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.mixins import (
    WorkflowSerializerMixin,
)
from pneumatic_backend.processes.services.urgent import (
    UrgentService
)
from pneumatic_backend.generics.fields import (
    AccountPrimaryKeyRelatedField,
    TimeStampField,
)
from pneumatic_backend.processes.utils.common import (
    contains_fields_vars,
    insert_kickoff_fields_vars,
)


UserModel = get_user_model()


class WorkflowListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'status',
            'tasks_count',
            'current_task',
            'active_tasks_count',  # TODO Remove in  41258
            'active_current_task',  # TODO Remove in  41258
            'template',
            'owners',
            'task',  # TODO Remove in  41258
            'is_legacy_template',
            'legacy_template_name',
            'passed_tasks',  # TODO Remove in  41258
            'tasks',
            'is_external',
            'is_urgent',
            'finalizable',
            'workflow_starter',
            'status_updated',
            'status_updated_tsp',
            'due_date_tsp',
            'date_created',
            'date_created_tsp',
            'date_completed',
            'date_completed_tsp',
            'fields',
        )

    task = serializers.SerializerMethodField()  # TODO Remove in  41258
    template = WorkflowTemplateSerializer()
    passed_tasks = serializers.SerializerMethodField()  # TODO Remove in  41258
    tasks = serializers.SerializerMethodField()
    fields = serializers.SerializerMethodField(
        method_name='get_filtered_fields'
    )
    owners = serializers.SerializerMethodField()
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    date_completed_tsp = TimeStampField(
        source='date_completed',
        read_only=True
    )
    status_updated_tsp = TimeStampField(
        source='status_updated',
        read_only=True
    )
    workflow_starter = serializers.IntegerField(
        read_only=True,
        source='workflow_starter_id'
    )

    def get_passed_tasks(self, instance: Workflow):
        #  TODO Remove in  41258
        tasks = instance.passed_tasks
        return TasksPassedInfoSerializer(instance=tasks, many=True).data

    def get_task(self, instance: Workflow):
        #  TODO Remove in  41258
        task = instance.current_tasks[0]
        data = WorkflowCurrentTaskSerializer(instance=task).data
        return data

    def get_tasks(self, instance: Workflow):
        tasks = instance.active_tasks
        return WorkflowCurrentTaskSerializer(instance=tasks, many=True).data

    def get_filtered_fields(self, instance: Workflow):
        if hasattr(instance, 'filtered_fields'):
            return TaskFieldListSerializer(
                instance=instance.filtered_fields,
                many=True
            ).data
        return []

    def get_owners(self, instance: Workflow):
        return list(e.id for e in instance.owners_ids)


class WorkflowCreateSerializer(
    CustomValidationErrorMixin,
    WorkflowSerializerMixin,
    serializers.ModelSerializer
):

    """ Use next context vars:
        * user - request user
        * redefined_performer - the user who will be appointed
          as the performer of the task instead of performers from task template
        * automatically_created - True for system created workflows
        """

    class Meta:
        model = Workflow
        fields = (
            'name',
            'is_urgent',
            'kickoff',
            'due_date_tsp',
            'ancestor_task_id',
        )

    name = serializers.CharField(required=False, allow_null=True)
    is_urgent = serializers.BooleanField(default=False)
    kickoff = serializers.DictField(
        required=False,
        allow_empty=True,
        allow_null=True
    )
    due_date_tsp = TimeStampField(required=False, allow_null=True)
    ancestor_task_id = AccountPrimaryKeyRelatedField(
        required=False,
        queryset=Task.objects.prefetch_related('performers').select_related(
            'workflow'
        )
    )

    def validate_due_date(self, value):
        if value and value <= timezone.now():
            raise ValidationError(messages.MSG_PW_0051)
        return value

    def validate_due_date_tsp(self, value):
        if value and value <= timezone.now():
            raise ValidationError(messages.MSG_PW_0051)
        return value

    def validate_ancestor_task_id(self, value: Task):
        user = self.context['user']
        if value.workflow.status == WorkflowStatus.DELAYED:
            raise ValidationError(messages.MSG_PW_0072)
        if value.is_completed:
            raise ValidationError(messages.MSG_PW_0073)
        if value.workflow.current_task != value.number:
            raise ValidationError(messages.MSG_PW_0074)
        allowed_performer = user.is_user and (
            user.is_account_owner or
            value.taskperformer_set.by_user_or_group(
                user.id
            ).exclude_directly_deleted().exists()
        )
        if not allowed_performer:
            raise ValidationError(messages.MSG_PW_0075)
        return value

    def validate(self, data):
        onboarding_workflow = self.context.get('automatically_created') is True
        template = self.context['template']
        if not template.is_active and not onboarding_workflow:
            raise ValidationError(messages.MSG_PW_0066)
        data['kickoff'] = data.get('kickoff', {}) or {}
        return data


class WorkflowUpdateSerializer(
    CustomValidationErrorMixin,
    WorkflowSerializerMixin,
    serializers.ModelSerializer
):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'is_urgent',
            'kickoff',
            'due_date_tsp',
        )

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=False)
    kickoff = serializers.DictField(
        required=False,
        allow_empty=True,
    )
    is_urgent = serializers.BooleanField(required=False)
    due_date_tsp = TimeStampField(required=False, allow_null=True)

    def validate_due_date(self, value):
        if value and value <= timezone.now():
            raise ValidationError(messages.MSG_PW_0051)
        return value

    def validate_due_date_tsp(self, value):
        if value and value <= timezone.now():
            raise ValidationError(messages.MSG_PW_0051)
        return value

    def update(
        self,
        instance: Workflow,
        validated_data: Dict[str, Any]
    ):
        update_kickoff_kwargs = {}
        update_tasks_kwargs = {}
        update_instance_kwargs = {}

        is_urgent = validated_data.get('is_urgent')
        is_urgent_changed = (
            is_urgent is not None and is_urgent != self.instance.is_urgent
        )
        name = validated_data.get('name')
        kickoff_fields_data = validated_data.get('kickoff')
        if name:
            update_instance_kwargs['name'] = name
            update_instance_kwargs['name_template'] = name

        if (
            'due_date_tsp' in validated_data
            and validated_data['due_date_tsp'] != self.instance.due_date
        ):
            update_instance_kwargs['due_date'] = validated_data['due_date_tsp']

        if is_urgent_changed:
            update_instance_kwargs['is_urgent'] = is_urgent
            update_tasks_kwargs['is_urgent'] = is_urgent
        if kickoff_fields_data:
            update_kickoff_kwargs['fields_data'] = kickoff_fields_data
            update_tasks_kwargs['fields_data'] = kickoff_fields_data

        with transaction.atomic():
            if update_instance_kwargs:
                self.instance = self._partial_update_workflow(
                    **update_instance_kwargs
                )
            if update_kickoff_kwargs:
                self._update_kickoff_value(
                    **update_kickoff_kwargs
                )
                if contains_fields_vars(self.instance.name_template):
                    self.instance.name = insert_kickoff_fields_vars(
                        self.instance
                    )
                    self.instance.save(update_fields=['name'])

            if update_tasks_kwargs:
                self._update_tasks(
                    is_urgent=is_urgent,
                    update_fields_values=bool(kickoff_fields_data)
                )
            if is_urgent_changed:
                UrgentService.resolve(
                    workflow=self.instance,
                    user=self.context['user']
                )
        return self.instance


class WorkflowCompleteSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    task_id = serializers.IntegerField(required=False)
    task_api_name = serializers.CharField(required=False)
    output = serializers.DictField(
        write_only=True,
        allow_empty=True,
        allow_null=False,
        required=False
    )

    def validate(self, attrs):
        workflow = self.context['workflow']
        if workflow.status == WorkflowStatus.DELAYED:
            raise ValidationError(messages.MSG_PW_0004)
        elif workflow.is_completed:
            raise ValidationError(messages.MSG_PW_0008)

        task = workflow.current_task_instance
        task_id = attrs.get('task_id')
        task_api_name = attrs.get('task_api_name')
        if not (task_id or task_api_name):
            raise ValidationError(messages.MSG_PW_0076)
        if task_id and task.id != task_id:
            # TODO Update message in https://my.pneumatic.app/workflows/35698/
            raise ValidationError(messages.MSG_PW_0018)
        if task_api_name and task.api_name != task_api_name:
            # TODO Update message in https://my.pneumatic.app/workflows/35698/
            raise ValidationError(messages.MSG_PW_0018)
        if not task.checklists_completed:
            raise ValidationError(messages.MSG_PW_0006)
        elif task.sub_workflows.running().exists():
            raise ValidationError(messages.MSG_PW_0070)

        user = self.context['user']
        task_performer = (
            TaskPerformer.objects
            .by_task(task.id)
            .by_user_or_group(user.id)
            .exclude_directly_deleted()
            .first()
        )
        if task_performer:
            if task_performer.is_completed:
                raise ValidationError(messages.MSG_PW_0007)
        elif not user.is_account_owner:
            raise ValidationError(messages.MSG_PW_0011)

        attrs['output'] = attrs.get('output') or {}
        attrs['task'] = task
        return attrs


class WorkflowReturnToTaskSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    task = serializers.IntegerField(required=False)
    task_api_name = serializers.CharField(required=False)

    def validate(self, data):
        workflow = self.context['workflow']
        task_id = data.get('task')
        task_api_name = data.get('task_api_name')

        if not (task_id or task_api_name):
            raise ValidationError(messages.MSG_PW_0076)
        try:
            if task_id:
                data['task'] = workflow.tasks.get(id=task_id)
            else:
                data['task'] = workflow.tasks.get(api_name=task_api_name)
        except ObjectDoesNotExist:
            raise ValidationError(messages.MSG_PW_0077)
        return data


class WorkflowFinishSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = Workflow
        fields = ()

    def additional_validate(self, data: Dict[str, Any], **kwargs):
        if self.instance.is_completed:
            self.raise_validation_error(message=messages.MSG_PW_0008)

        if not self.instance.finalizable:
            self.raise_validation_error(message=messages.MSG_PW_0009)
        user = self.context['user']
        if not self.instance.can_be_finished_by(user):
            self.raise_validation_error(message=messages.MSG_PW_0009)

    def update(self, instance: Workflow, validated_data):
        self.additional_validate(validated_data)

        with transaction.atomic():
            service = WorkflowActionService(
                workflow=instance,
                user=self.context['user'],
                is_superuser=self.context['is_superuser'],
                auth_type=self.context['auth_type'],
            )
            service.end_process(by_condition=False, by_complete_task=False)
        return instance


class WorkflowDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'description',
            'template',
            'owners',
            'current_task',  # TODO Remove in  41258
            'tasks_count',
            'active_tasks_count',  # TODO Remove in  41258
            'active_current_task',  # TODO Remove in  41258
            'workflow_starter',
            'finalizable',
            'is_legacy_template',
            'legacy_template_name',
            'status',
            'kickoff',
            'is_external',
            'is_urgent',
            'passed_tasks',  # TODO Remove in  41258
            'date_completed',
            'date_completed_tsp',
            'due_date_tsp',
            'date_created',
            'date_created_tsp',
            'ancestor_task_id',
            'tasks',
        )

    template = TemplateDetailsSerializer()
    current_task = serializers.SerializerMethodField()
    workflow_starter = serializers.IntegerField(
        source='workflow_starter_id',
        read_only=True
    )
    kickoff = serializers.SerializerMethodField()
    #  TODO Remove in  41258
    passed_tasks = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    date_completed_tsp = TimeStampField(
        source='date_completed',
        read_only=True
    )

    def get_passed_tasks(self, instance: Workflow):
        #  TODO Remove in  41258
        return TasksPassedInfoSerializer(
            instance.tasks.completed().order_by('number'),
            many=True
        ).data

    def get_kickoff(self, instance: Workflow):
        kickoff = instance.kickoff_instance
        if kickoff:
            return KickoffValueInfoSerializer(kickoff).data
        return None

    def get_current_task(self, instance: Workflow):
        #  TODO Remove in  41258
        task = instance.tasks.get(number=instance.current_task)
        return WorkflowCurrentTaskSerializer(instance=task).data

    def get_tasks(self, instance: Workflow):
        tasks = instance.tasks.exclude(status=TaskStatus.SKIPPED)
        return WorkflowCurrentTaskSerializer(instance=tasks, many=True).data


class WorkflowNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
        )


class WorkflowListFilterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    serializers.Serializer
):

    status = serializers.ChoiceField(
        required=False,
        choices=WorkflowApiStatus.CHOICES
    )
    template_id = serializers.CharField(required=False)
    template_task_api_name = serializers.CharField(required=False)
    fields = serializers.CharField(required=False)
    # TODO Remove in https://my.pneumatic.app/workflows/36988/
    template_task_id = serializers.CharField(required=False)
    current_performer = serializers.CharField(required=False)
    current_performer_group_ids = serializers.CharField(required=False)
    workflow_starter = serializers.CharField(required=False)
    ordering = serializers.ChoiceField(
        required=False,
        choices=WorkflowOrdering.CHOICES
    )
    search = serializers.CharField(required=False)
    is_external = serializers.BooleanField(
        required=False,
        default=None,
        allow_null=True
    )
    limit = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=WorkflowListPagination.max_limit,
        default=WorkflowListPagination.default_limit
    )
    offset = serializers.IntegerField(
        required=False,
        min_value=0,
    )

    def validate_template_id(self, value):
        return self.get_valid_list_integers(value)

    def validate_template_task_api_name(self, value):
        return self.get_valid_list_strings(value)

    def validate_fields(self, value):
        return self.get_valid_list_strings(value)

    # TODO Remove in https://my.pneumatic.app/workflows/36988/
    def validate_template_task_id(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer_group_ids(self, value):
        return self.get_valid_list_integers(value)

    def validate_workflow_starter(self, value):
        return self.get_valid_list_integers(value)

    def validate_search(self, value: str) -> str:
        removed_chars_regex = r'\s\s+'
        clear_text = re.sub(removed_chars_regex, '', value).strip()
        return clear_text if clear_text else None

    def validate(self, data):
        # TODO Remove in https://my.pneumatic.app/workflows/36988/
        template_task_ids = data.get('template_task_id')
        if template_task_ids:
            data['template_task_api_name'] = (
                TaskTemplate.objects
                .filter(id__in=template_task_ids)
                .values_list('api_name', flat=True)
            )
        data.pop('template_task_id', None)
        status = data.get('status')
        current_performer = data.get('current_performer')
        current_performer_group_ids = data.get('current_performer_group_ids')
        if (
            (current_performer or current_performer_group_ids)
            and status in WorkflowApiStatus.NOT_RUNNING
        ):
            raise ValidationError(messages.MSG_PW_0067)
        return data


class WorkflowFieldsFilterSerializer(
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    serializers.Serializer
):

    status = serializers.ChoiceField(
        required=False,
        allow_null=False,
        choices=WorkflowApiStatus.CHOICES
    )
    template_id = serializers.IntegerField(
        required=False,
        allow_null=False,
        validators=[MinValueValidator(1)]
    )
    fields = serializers.CharField(required=False)
    limit = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=DefaultPagination.max_limit,
        default=DefaultPagination.default_limit
    )
    offset = serializers.IntegerField(
        required=False,
        min_value=0,
    )

    def validate_status(self, value):
        return WorkflowApiStatus.MAP[value]

    def validate_fields(self, value):
        return self.get_valid_list_strings(value)


class WorkflowFieldsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'status',
            'date_created',
            'date_created_tsp',
            'date_completed',
            'date_completed_tsp',
            'fields',
        )

    fields = TaskFieldListSerializer(many=True)
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    date_completed_tsp = TimeStampField(
        source='date_completed',
        read_only=True
    )


class WorkflowSnoozeSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    date = serializers.DateTimeField(required=True)


class WorkflowRevertSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def validate(self, data):
        comment = data.get('comment', '').strip()
        if not comment:
            raise ValidationError(messages.MSG_PW_0083)
        return data
