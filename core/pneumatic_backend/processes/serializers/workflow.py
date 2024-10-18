# pylint: disable=comparison-with-callable
import re
from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.generics.mixins.serializers import (
    CustomValidationErrorMixin,
    ValidationUtilsMixin,
    AdditionalValidationMixin,
)
from pneumatic_backend.processes.models import (
    Template,
    Workflow,
    TaskPerformer,
    Task,
    Delay,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    WorkflowApiStatus,
    WorkflowOrdering,
    DirectlyStatus,
)
from pneumatic_backend.processes.serializers.kickoff_value import (
    KickoffValueInfoSerializer,
)
from pneumatic_backend.processes.serializers.template import (
    TemplateDetailsSerializer,
)
from pneumatic_backend.processes.serializers.task_field import (
    WorkflowTaskFieldSerializer,
)
from pneumatic_backend.processes.services.websocket import WSSender
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.task import (
    TasksPassedInfoSerializer,
    WorkflowCurrentTaskSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.workflow.mixins import (
    WorkflowSerializerMixin,
    BaseWorkflowRevertSerializerMixin
)
from pneumatic_backend.processes.services.urgent import (
    UrgentService
)
from pneumatic_backend.generics.fields import (
    AccountPrimaryKeyRelatedField,
    TimeStampField,
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.processes.tasks.webhooks import (
    send_task_webhook,
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
            'template',
            'task',
            'is_legacy_template',
            'legacy_template_name',
            'passed_tasks',
            'is_external',
            'is_urgent',
            'finalizable',
            'workflow_starter',
            'status_updated',
            'status_updated_tsp',
            'due_date',
            'due_date_tsp',
            'date_created',
            'date_created_tsp',
            'date_completed',
            'date_completed_tsp',
        )

    task = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()
    passed_tasks = serializers.SerializerMethodField()
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

    def get_template(self, instance: Workflow):
        return {
            'id': instance.template_id,
            'name': instance.template_name,
            'is_active': instance.template_is_active,
            'template_owners': list(
                Template.template_owners.through.objects.filter(
                    template_id=instance.template_id
                ).order_by('user_id').values_list('user_id', flat=True)
            )
        }

    def get_passed_tasks(self, instance: Workflow):
        return TasksPassedInfoSerializer(
            instance.tasks.completed().order_by('number'),
            many=True
        ).data

    def get_task(self, instance: Workflow):
        data = {
            'id': instance.task_id,
            'name': instance.task_name,
            'number': instance.task_number,
            'due_date': instance.task_due_date,
            'due_date_tsp': (
                instance.task_due_date.timestamp() if
                instance.task_due_date else None
            ),
            'date_started':  instance.task_date_started,
            'date_started_tsp': (
                instance.task_date_started.timestamp() if
                instance.task_date_started else None
            ),
            'checklists_total': instance.task_checklists_total,
            'checklists_marked': instance.task_checklists_marked,
            'delay': None,
            'performers': list(
                TaskPerformer.objects.by_task(
                    instance.task_id
                ).exclude_directly_deleted().user_ids()
            ),
        }
        if instance.status == WorkflowStatus.DELAYED:
            data['delay'] = {
                'duration': instance.delay_duration,
                'start_date': instance.delay_start_date,
                'start_date_tsp': (
                    instance.delay_start_date.timestamp() if
                    instance.delay_start_date else None
                ),
                'end_date': instance.delay_end_date,
                'end_date_tsp': (
                    instance.delay_end_date.timestamp() if
                    instance.delay_end_date else None
                ),
            }
        return data


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
            'due_date',
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
    due_date = serializers.DateTimeField(required=False, allow_null=True)
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
            value.taskperformer_set.by_user(
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
        data['due_date'] = data.get('due_date_tsp', data.get('due_date'))
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
            'due_date',
            'due_date_tsp',
        )

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=False)
    kickoff = serializers.DictField(
        required=False,
        allow_empty=True,
    )
    is_urgent = serializers.BooleanField(required=False)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
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
        elif (
            'due_date' in validated_data
            and validated_data['due_date'] != self.instance.due_date
        ):
            update_instance_kwargs['due_date'] = validated_data['due_date']

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

    task_id = serializers.IntegerField()
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
        elif workflow.status in WorkflowStatus.END_STATUSES:
            raise ValidationError(messages.MSG_PW_0008)

        task = workflow.current_task_instance
        if task.id != attrs['task_id']:
            raise ValidationError(messages.MSG_PW_0018)
        elif not task.checklists_completed:
            raise ValidationError(messages.MSG_PW_0006)
        elif task.sub_workflows.running().exists():
            raise ValidationError(messages.MSG_PW_0070)

        user = self.context['user']
        task_performer = (
            TaskPerformer.objects
            .by_task(task.id)
            .by_user(user.id)
            .exclude_directly_deleted()
            .first()
        )
        if task_performer:
            if task_performer.is_completed:
                raise ValidationError(messages.MSG_PW_0007)
        elif not user.is_account_owner:
            raise ValidationError(messages.MSG_PW_0011)

        attrs['output'] = attrs.get('output') or {}
        return attrs


class WorkflowRevertSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
    BaseWorkflowRevertSerializerMixin,
):

    class Meta:
        model = Workflow
        fields = ()

    def validate(self, attrs):
        current_task = self.instance.current_task_instance
        if (
            not current_task.is_returnable or
            self.instance.status != WorkflowStatus.RUNNING
        ):
            raise ValidationError(messages.MSG_PW_0012)
        if current_task.sub_workflows.running().exists():
            raise ValidationError(messages.MSG_PW_0071)
        return attrs

    def update(self, instance: Workflow, validated_data):

        """ TODO Move to WorkflowActionService.return_to in
              https://my.pneumatic.app/workflows/23046/ """

        user = self.context.get('user')
        current_task = instance.current_task_instance
        previous_task = current_task.prev
        with transaction.atomic():
            current_task.date_started = None
            current_task.date_completed = None
            current_task.is_completed = False
            current_task.is_skipped = False
            current_task.save(
                update_fields=[
                    'date_started',
                    'date_completed',
                    'is_completed',
                    'is_skipped'
                ]
            )
            current_task.taskperformer_set.exclude_directly_deleted().update(
                is_completed=False,
                date_completed=None
            )
            WorkflowEventService.task_revert_event(
                task=previous_task,
                user=user
            )
            self._update_workflow(
                workflow=instance,
                current_task=current_task,
            )
            workflow_action_service = WorkflowActionService()
            action_method, by_cond = workflow_action_service.execute_condition(
                previous_task
            )
            action_method(
                workflow=instance,
                task=previous_task,
                user=user,
                is_reverted=True,
                by_condition=by_cond,
            )
        WSSender.send_removed_task_notification(current_task)
        AnalyticService.task_returned(
            user=user,
            task=current_task,
            is_superuser=self.context['is_superuser'],
            auth_type=self.context['auth_type']
        )
        send_task_webhook.delay(
            event_name='task_returned',
            user_id=user.id,
            instance_id=previous_task.id
        )
        return instance


class WorkflowReturnToTaskSerializer(
    CustomValidationErrorMixin,
    serializers.ModelSerializer,
    BaseWorkflowRevertSerializerMixin,
):

    class Meta:
        model = Workflow
        fields = ('task',)

    task = AccountPrimaryKeyRelatedField(queryset=Task.objects.all())

    def validate(self, attrs):
        if (
            self.instance.current_task == 1 and
            self.instance.status != WorkflowStatus.DONE
        ):
            raise ValidationError(messages.MSG_PW_0012)
        current_task = self.instance.current_task_instance
        if current_task.sub_workflows.running().exists():
            raise ValidationError(messages.MSG_PW_0071)
        return attrs

    def validate_task(self, value):

        revert_to_task = value
        if self.instance.current_task < revert_to_task.number or (
            self.instance.current_task == revert_to_task.number and
            self.instance.status != WorkflowStatus.DONE
        ):
            raise ValidationError(messages.MSG_PW_0013)
        return value

    def update(self, instance: Workflow, validated_data):

        """ TODO Move to WorkflowActionService.return_to in
              https://my.pneumatic.app/workflows/23046/ """

        user = self.context.get('user')
        revert_to_task = validated_data['task']

        task_revert_from = instance.current_task_instance
        next_tasks = instance.tasks.filter(number__gt=revert_to_task.number)

        workflow_action_service = WorkflowActionService(
            user=user,
            auth_type=self.context['auth_type'],
            is_superuser=self.context['is_superuser']
        )
        action_method, by_cond = workflow_action_service.execute_condition(
            revert_to_task
        )
        if action_method == workflow_action_service.skip_task:
            self.raise_validation_error(message=messages.MSG_PW_0012)

        with transaction.atomic():
            WorkflowEventService.workflow_revert_event(
                task=task_revert_from,
                user=user,
            )
            next_tasks.update(
                date_started=None,
                date_completed=None,
                is_completed=False,
                is_skipped=False
            )
            TaskPerformer.objects.with_tasks_after(
                revert_to_task
            ).by_workflow(
                instance.id
            ).exclude_directly_deleted().update(
                is_completed=False,
                date_completed=None
            )
            Delay.objects.filter(
                task__in=next_tasks,
                directly_status=DirectlyStatus.NO_STATUS
            ).update(
                start_date=None,
                end_date=None,
                estimated_end_date=None,
            )
            workflow_is_running = instance.is_running
            self._update_workflow(
                workflow=instance,
                current_task=task_revert_from,
                reverted_to=revert_to_task.number
            )
            if workflow_is_running:
                WSSender.send_removed_task_notification(task_revert_from)
            AnalyticService.workflow_returned(
                user=user,
                task=revert_to_task,
                workflow=self.instance,
                is_superuser=self.context['is_superuser'],
                auth_type=self.context['auth_type'],
            )
            action_method(
                workflow=instance,
                task=revert_to_task,
                user=user,
                is_reverted=True,
                by_condition=by_cond,
            )
        send_task_webhook.delay(
            event_name='task_returned',
            user_id=user.id,
            instance_id=revert_to_task.id
        )
        return instance


class WorkflowFinishSerializer(
    CustomValidationErrorMixin,
    AdditionalValidationMixin,
    serializers.ModelSerializer,
):

    class Meta:
        model = Workflow
        fields = ()

    def additional_validate(self, data: Dict[str, Any], **kwargs):
        if self.instance.status in WorkflowStatus.END_STATUSES:
            self.raise_validation_error(message=messages.MSG_PW_0008)

        if not self.instance.finalizable:
            self.raise_validation_error(message=messages.MSG_PW_0009)
        user = self.context['user']
        if not self.instance.can_be_finished_by(user):
            self.raise_validation_error(message=messages.MSG_PW_0009)

    def update(self, instance: Workflow, validated_data):
        self.additional_validate(validated_data)

        with transaction.atomic():
            WorkflowActionService().end_process(
                workflow=instance,
                user=self.context['user'],
                by_condition=False,
                by_complete_task=False,
            )
        return instance


class WorkflowDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'description',
            'template',
            'current_task',
            'tasks_count',
            'workflow_starter',
            'finalizable',
            'is_legacy_template',
            'legacy_template_name',
            'status',
            'kickoff',
            'is_external',
            'is_urgent',
            'passed_tasks',
            'date_completed',
            'date_completed_tsp',
            'due_date',
            'due_date_tsp',
            'date_created',
            'date_created_tsp',
            'ancestor_task_id',
        )

    template = TemplateDetailsSerializer()
    current_task = serializers.SerializerMethodField()
    workflow_starter = serializers.IntegerField(
        source='workflow_starter_id',
        read_only=True
    )
    kickoff = serializers.SerializerMethodField()
    passed_tasks = serializers.SerializerMethodField()
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    date_completed_tsp = TimeStampField(
        source='date_completed',
        read_only=True
    )

    def get_passed_tasks(self, instance: Workflow):
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
        task = instance.tasks.get(number=instance.current_task)
        return WorkflowCurrentTaskSerializer(
            instance=task,
            context={'with_delay': instance.is_delayed}
        ).data


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
    template_task_id = serializers.CharField(required=False)
    current_performer = serializers.CharField(required=False)
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

    def validate_template_id(self, value):
        return self.get_valid_list_integers(value)

    def validate_template_task_id(self, value):
        return self.get_valid_list_integers(value)

    def validate_current_performer(self, value):
        return self.get_valid_list_integers(value)

    def validate_workflow_starter(self, value):
        return self.get_valid_list_integers(value)

    def validate_search(self, value: str) -> str:
        removed_chars_regex = r'\s\s+'
        clear_text = re.sub(removed_chars_regex, '', value).strip()
        return clear_text if clear_text else None

    def validate(self, data):
        status = data.get('status')
        current_performer = data.get('current_performer')
        if current_performer and status in WorkflowApiStatus.NOT_RUNNING:
            raise ValidationError(messages.MSG_PW_0067)
        return data


class WorkflowFieldsSerializer(
    serializers.ModelSerializer
):
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
            'fields'
        )

    fields = WorkflowTaskFieldSerializer(many=True)
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
