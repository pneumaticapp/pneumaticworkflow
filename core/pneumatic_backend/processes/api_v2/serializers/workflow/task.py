import re
from typing import List, Optional
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from pneumatic_backend.processes.models import (
    Delay,
    Task,
    TaskPerformer,
    TaskForList,
    Workflow,
)
from pneumatic_backend.generics.fields import TimeStampField
from pneumatic_backend.processes.enums import TaskOrdering
from pneumatic_backend.processes.serializers.task_field import (
    TaskFieldListSerializer,
)
from pneumatic_backend.processes.api_v2.serializers.workflow\
    .checklist import CheckListSerializer

from pneumatic_backend.processes.serializers.delay import DelayInfoSerializer
from pneumatic_backend.processes.serializers.template import (
    TemplateDetailsSerializer,
)
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0057,
)


class WorkflowCurrentTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'number',
            'delay',
            'due_date',
            'due_date_tsp',
            'date_started',
            'date_started_tsp',
            'performers',
            'checklists_total',
            'checklists_marked',
        )

    delay = serializers.SerializerMethodField()
    performers = serializers.SerializerMethodField()
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    date_started_tsp = TimeStampField(source='date_started', read_only=True)

    def get_delay(self, instance):
        if self.context.get('with_delay'):
            delay = Delay.objects.current_task_delay(instance)
            if delay:
                return DelayInfoSerializer(delay).data
        return None

    def get_performers(self, instance) -> List[int]:
        return list(
            TaskPerformer.objects.by_task(
                instance.id
            ).exclude_directly_deleted().user_ids()
        )


class TasksPassedInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'number'
        )


class WorkflowShortInfoSerializer(serializers.ModelSerializer):

    """ Used for tasks API only """

    class Meta:
        model = Workflow
        fields = (
            'id',
            'status',
            'name',
            'current_task',
            'template_name',
            'date_completed',
            'date_completed_tsp',
        )

    template_name = serializers.SerializerMethodField()
    date_completed_tsp = TimeStampField(source='date_completed')

    def get_template_name(self, instance: Workflow):
        if instance.is_legacy_template:
            return instance.legacy_template_name
        else:
            return instance.template.name


class WorkflowInfoSerializer(serializers.ModelSerializer):

    """ Used for tasks API only """

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'description',
            'task',
            'current_task',
            'tasks_count',
            'workflow_starter',
            'finalizable',
            'status',
            'is_external',
            'is_urgent',
            'passed_tasks',
            'date_completed',
            'date_completed_tsp',
            'due_date',
            'due_date_tsp',
            'date_created',
            'date_created_tsp',
            'template',
        )

    task = serializers.SerializerMethodField()
    workflow_starter = serializers.IntegerField(
        source='workflow_starter_id',
        read_only=True
    )
    passed_tasks = serializers.SerializerMethodField()
    due_date_tsp = TimeStampField(source='due_date', read_only=True)
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    date_completed_tsp = TimeStampField(
        source='date_completed',
        read_only=True
    )
    template = TemplateDetailsSerializer(read_only=True)

    def get_passed_tasks(self, instance: Workflow):
        return TasksPassedInfoSerializer(
            instance.tasks.completed().order_by('number'),
            many=True
        ).data

    def get_task(self, instance: Workflow):
        task = instance.tasks.get(number=instance.current_task)
        return WorkflowCurrentTaskSerializer(
            instance=task,
            context={'with_delay': instance.is_delayed}
        ).data


class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'description',
            'workflow',
            'contains_comments',
            'require_completion_by_all',
            'output',
            'delay',
            'date_started',
            'date_started_tsp',
            'is_completed',
            'date_completed',
            'date_completed_tsp',
            'due_date',
            'due_date_tsp',
            'performers',
            'is_urgent',
            'checklists_marked',
            'checklists_total',
            'checklists',
            'sub_workflows',
        )

    date_started_tsp = TimeStampField(source='date_started')
    date_completed_tsp = TimeStampField(source='date_completed')
    performers = serializers.SerializerMethodField()
    workflow = WorkflowShortInfoSerializer(read_only=True)
    output = TaskFieldListSerializer(many=True)
    delay = serializers.SerializerMethodField(required=False, allow_null=True)
    is_completed = serializers.SerializerMethodField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    checklists_marked = serializers.IntegerField(read_only=True)
    checklists_total = serializers.IntegerField(read_only=True)
    checklists = CheckListSerializer(many=True, read_only=True)
    due_date = serializers.DateTimeField(read_only=True, allow_null=True)
    due_date_tsp = TimeStampField(source='due_date')
    sub_workflows = WorkflowInfoSerializer(many=True, read_only=True)

    def get_performers(self, instance) -> List[int]:
        return list(
            TaskPerformer.objects.by_task(
                instance.id
            ).exclude_directly_deleted().user_ids()
        )

    def get_is_completed(self, instance):
        if instance.is_completed:
            return True

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
        delay = Delay.objects.current_task_delay(instance)
        if delay:
            return DelayInfoSerializer(delay).data
        return None


class TaskListSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskForList
        fields = (
            'id',
            'name',
            'workflow_name',
            'due_date',
            'due_date_tsp',
            'date_started',
            'date_started_tsp',
            'date_completed',
            'date_completed_tsp',
            'template_id',
            'template_task_id',
            'is_urgent'
        )


class TaskListFilterSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    is_completed = serializers.BooleanField(default=False, required=False)
    ordering = serializers.ChoiceField(
        required=False,
        choices=TaskOrdering.CHOICES
    )
    assigned_to = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False)
    template_id = serializers.IntegerField(required=False)
    template_task_id = serializers.IntegerField(required=False)
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
