from rest_framework import serializers

from src.generics.fields import TimeStampField
from src.processes.enums import WorkflowEventType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Delay, Task
from src.processes.models.workflows.workflow import Workflow
from src.storage.models import Attachment
from src.storage.utils import extract_file_ids_from_text
from src.processes.serializers.workflows.field import (
    TaskFieldSerializer,
)
from src.processes.serializers.workflows.task_performer import (
    TaskUserGroupPerformerSerializer,
)


class SubWorkflowEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = (
            'id',
            'name',
            'description',
            'date_created',
            'date_created_tsp',
            'due_date_tsp',
            'is_urgent',
        )
    date_created_tsp = TimeStampField(source='date_created', read_only=True)
    due_date_tsp = TimeStampField(source='due_date', read_only=True)


class DelayEventJsonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Delay
        fields = (
            'id',
            'duration',
            'start_date',
            'end_date',
            'estimated_end_date',
            'start_date_tsp',
            'end_date_tsp',
            'estimated_end_date_tsp',
        )

    start_date_tsp = TimeStampField(source='start_date')
    end_date_tsp = TimeStampField(source='end_date', read_only=True)
    estimated_end_date_tsp = TimeStampField(
        source='estimated_end_date',
        read_only=True,
    )


class TaskEventJsonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'id',
            'number',
            'name',
            'description',
            'performers',
            'due_date_tsp',
            'output',
            'sub_workflow',
        )

    performers = TaskUserGroupPerformerSerializer(
        many=True,
        source='exclude_directly_deleted_taskperformer_set',
    )
    output = serializers.SerializerMethodField()
    due_date_tsp = TimeStampField(source='due_date')
    sub_workflow = serializers.SerializerMethodField()

    def get_output(self, instance):
        if self.context['event_type'] == WorkflowEventType.TASK_COMPLETE:
            return TaskFieldSerializer(
                instance=instance.output.all(),
                many=True,
            ).data
        return None

    def get_sub_workflow(self, instance):
        if self.context['event_type'] == WorkflowEventType.SUB_WORKFLOW_RUN:
            return SubWorkflowEventSerializer(
                instance=self.context['sub_workflow'],
            ).data
        return None


class EventAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for attachments in workflow events."""

    class Meta:
        model = Attachment
        fields = [
            'id',
            'file_id',
            'access_type',
            'source_type',
        ]


class WorkflowEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowEvent
        fields = (
            'id',
            'created',
            'created_tsp',
            'updated',
            'updated_tsp',
            'status',
            'text',
            'type',
            'user_id',
            'target_user_id',
            'target_group_id',
            'delay',
            'task',
            'attachments',
            'workflow_id',
            'watched',
            'reactions',
        )
    task = serializers.JSONField(source='task_json')
    delay = serializers.JSONField(source='delay_json')
    attachments = serializers.SerializerMethodField()
    created_tsp = TimeStampField(source='created')
    updated_tsp = TimeStampField(source='updated')

    def get_attachments(self, instance):
        """Get attachments mentioned in the event text."""

        if not instance.text:
            return []

        # Extract file IDs from event text
        file_ids = extract_file_ids_from_text(instance.text)
        if not file_ids:
            return []

        # Get attachments by file_ids
        attachments = Attachment.objects.filter(
            file_id__in=file_ids,
            account=instance.account,
        )

        return EventAttachmentSerializer(attachments, many=True).data
