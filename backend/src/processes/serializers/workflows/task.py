# ruff: noqa: PLC0415
import re
from typing import Any, Dict, List, Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.generics.fields import TimeStampField
from src.generics.serializers import CustomValidationErrorMixin
from src.processes.enums import TaskOrdering
from src.processes.messages.workflow import (
    MSG_PW_0057,
    MSG_PW_0083,
)
from src.processes.models.workflows.task import (
    Task,
    TaskForList,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.workflows.checklist import (
    CheckListSerializer,
)
from src.processes.serializers.workflows.delay import (
    DelayInfoSerializer,
)
from src.processes.serializers.workflows.field import (
    TaskFieldSerializer,
)
from src.processes.serializers.workflows.task_performer import (
    TaskUserGroupPerformerSerializer,
)


class TaskShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'api_name',
        )


class WorkflowCurrentTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'api_name',
            'description',
            'number',
            'delay',
            'due_date_tsp',
            'date_started_tsp',
            'date_completed_tsp',
            'performers',
            'checklists_total',
            'checklists_marked',
            'status',
        )

    delay = serializers.SerializerMethodField()
    performers = serializers.SerializerMethodField()
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    date_started_tsp = TimeStampField(source='date_started', read_only=True)
    date_completed_tsp = TimeStampField(source='date_completed')

    def get_delay(self, instance: Task):
        if hasattr(instance, 'current_delay'):
            # GET /workflows qst prefetch delay to "current_delay" attribute
            if instance.current_delay:
                # Check that exists
                delay = instance.current_delay[0]
                return DelayInfoSerializer(delay).data
        else:
            delay = instance.get_active_delay()
            if delay:
                return DelayInfoSerializer(delay).data
        return None

    def get_performers(self, instance) -> List[Dict[str, Any]]:
        if hasattr(instance, 'all_performers'):
            performers = instance.all_performers
        else:
            performers = instance.exclude_directly_deleted_taskperformer_set()
        return TaskUserGroupPerformerSerializer(performers, many=True).data


class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'api_name',
            'description',
            'workflow',
            'contains_comments',
            'require_completion_by_all',
            'output',
            'delay',
            'date_started_tsp',
            'date_completed_tsp',
            'due_date_tsp',
            'is_completed',     # TODO deprecated
            'performers',
            'is_urgent',
            'checklists_marked',
            'checklists_total',
            'checklists',
            'sub_workflows',
            'status',
            'revert_tasks',
            'is_read_only_viewer',
        )

    date_started_tsp = TimeStampField(source='date_started')
    date_completed_tsp = TimeStampField(source='date_completed')
    performers = TaskUserGroupPerformerSerializer(
        many=True,
        source='exclude_directly_deleted_taskperformer_set',
    )
    workflow = serializers.SerializerMethodField()
    output = TaskFieldSerializer(many=True)
    delay = serializers.SerializerMethodField(required=False, allow_null=True)
    #  TODO Remove in 41258
    is_completed = serializers.SerializerMethodField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    checklists_marked = serializers.IntegerField(read_only=True)
    checklists_total = serializers.IntegerField(read_only=True)
    checklists = CheckListSerializer(many=True, read_only=True)
    due_date_tsp = TimeStampField(source='due_date')
    sub_workflows = serializers.SerializerMethodField()
    revert_tasks = TaskShortSerializer(many=True, source='get_revert_tasks')
    is_read_only_viewer = serializers.SerializerMethodField()

    def get_is_completed(self, instance):
        #  TODO Remove in 41258
        if instance.is_completed:
            return True
        if self.context.get('user'):
            user = self.context['user']

            user_completed_task = instance.taskperformer_set.filter(
                is_completed=True,
                user_id=user.id,
            )
            if (
                instance.require_completion_by_all and
                user_completed_task.exists()
            ):
                return True
        return False

    def get_delay(self, instance):
        delay = instance.get_active_delay()
        if delay:
            return DelayInfoSerializer(delay).data
        return None

    def get_sub_workflows(self, instance):
        qst = Workflow.objects.raw_list_query(
            account_id=instance.account_id,
            ancestor_task_id=instance.id,
        )
        from src.processes.serializers.workflows.workflow import (
            WorkflowListSerializer,
        )
        return WorkflowListSerializer(instance=qst, many=True).data

    def get_workflow(self, instance):
        from src.processes.serializers.workflows.workflow import (
            WorkflowShortInfoSerializer,
        )
        return WorkflowShortInfoSerializer(instance=instance.workflow).data

    def get_is_read_only_viewer(self, instance):
        """
        Determine if user has only read-only access via template viewer
        (not as workflow member, owner, or task performer).
        Template viewers who are assigned as task performers should have
        full access to the task (can comment, etc).
        """
        user = self.context.get('user')
        if not user or user.is_account_owner or user.is_admin:
            return False

        # Check if user is workflow member or owner
        workflow = instance.workflow
        is_workflow_member = (
            workflow.members.filter(id=user.id).exists() or
            workflow.owners.filter(id=user.id).exists()
        )

        if is_workflow_member:
            return False

        # Check if user is template owner
        from django.db.models import Q
        template = workflow.template
        is_template_owner = template.owners.filter(
            Q(type='user', user_id=user.id, is_deleted=False) |
            Q(type='group', group__users__id=user.id, is_deleted=False),
        ).exists()

        if is_template_owner:
            return False

        # Check if user is task performer
        from src.processes.models.workflows.task import TaskPerformer
        performer_user_ids = (
            TaskPerformer.objects
            .by_task(instance.id)
            .filter(task__account_id=user.account_id)
            .get_user_ids_set()
        )

        if user.id in performer_user_ids:
            return False

        # Check if user has access via template viewer
        return template.viewers.filter(
            Q(type='user', user_id=user.id, is_deleted=False)
            | Q(type='group', group__users__id=user.id, is_deleted=False),
        ).exists()


class TaskListSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskForList
        fields = (
            'id',
            'name',
            'api_name',
            'workflow_name',
            'due_date_tsp',
            'date_started_tsp',
            'date_completed_tsp',
            'template_id',
            'template_task_api_name',
            'is_urgent',
            'status',
        )


class TaskListFilterSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    is_completed = serializers.BooleanField(default=False, required=False)
    ordering = serializers.ChoiceField(
        required=False,
        choices=TaskOrdering.CHOICES,
    )
    assigned_to = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False)
    template_id = serializers.IntegerField(required=False)
    template_task_api_name = serializers.CharField(required=False)
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)

    def validate_search(self, value: str) -> Optional[str]:
        removed_chars_regex = r'\s\s+'
        clear_text = re.sub(removed_chars_regex, '', value).strip()
        return clear_text if clear_text else None

    def validate_assigned_to(self, value):
        if not self.context['user'].is_admin:
            raise ValidationError(MSG_PW_0057)
        return value


class TaskRevertSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    def validate(self, data):
        comment = data.get('comment', '').strip()
        if not comment:
            raise ValidationError(MSG_PW_0083)
        return data


class TaskCompleteSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer,
):

    output = serializers.DictField(required=False)
