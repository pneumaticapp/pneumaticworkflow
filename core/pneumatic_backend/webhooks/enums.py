
class HookEvent:

    WORKFLOW_COMPLETED = 'workflow_completed'
    WORKFLOW_STARTED = 'workflow_started'
    TASK_STARTED = 'task_completed_v2'
    TASK_RETURNED = 'task_returned'

    VALUES = {
        WORKFLOW_COMPLETED,
        WORKFLOW_STARTED,
        TASK_STARTED,
        TASK_RETURNED
    }

    CHOICES = {
        WORKFLOW_COMPLETED: WORKFLOW_COMPLETED,
        WORKFLOW_STARTED: WORKFLOW_STARTED,
        TASK_STARTED: TASK_STARTED,
        TASK_RETURNED: TASK_RETURNED
    }
