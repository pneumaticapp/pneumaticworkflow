"""OpenAPI projections for webhook payloads, never runtime serialization."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers

from src.openapi.parameters import query_param
from src.openapi.serializers import WebhookHookSerializer
from src.processes.enums import TaskStatus, WorkflowStatus
from src.processes.serializers.workflows.task import TaskSerializer
from src.processes.serializers.workflows.workflow import (
    WorkflowDetailsSerializer,
)


TASK_WEBHOOK_EXAMPLE_PARAMS = [
    query_param(
        'status',
        description='Filter by task status.',
        enum=[TaskStatus.ACTIVE, TaskStatus.COMPLETED],
    ),
    query_param(
        'ordering',
        description='Order tasks by their start date.',
        enum=['date_started', '-date_started'],
    ),
]


WORKFLOW_WEBHOOK_EXAMPLE_PARAMS = [
    OpenApiParameter(
        'status',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description='Legacy workflow status: 0 is running, 1 is done.',
        enum=[WorkflowStatus.RUNNING, WorkflowStatus.DONE],
    ),
    query_param(
        'ordering',
        description='Order workflows by their creation date.',
        enum=['date_created', '-date_created'],
    ),
]


class TaskWebhookPayloadSerializer(TaskSerializer):
    # webhook_payload replaces the task's short workflow with full details.
    workflow = WorkflowDetailsSerializer(read_only=True)


class TaskWebhookPayloadExampleSerializer(serializers.Serializer):
    hook = WebhookHookSerializer()
    task = TaskWebhookPayloadSerializer()
