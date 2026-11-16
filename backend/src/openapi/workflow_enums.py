"""Document all event values emitted by services, retaining runtime choices."""

from src.processes.enums import WorkflowEventType

WORKFLOW_EVENT_TYPE_CHOICES = (
    *WorkflowEventType.CHOICES,
    (WorkflowEventType.SUB_WORKFLOW_RUN, 'Subworkflow started'),
)
