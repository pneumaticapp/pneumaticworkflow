from typing_extensions import Literal


class HookEvent:

    WORKFLOW_COMPLETED = 'workflow_completed'
    WORKFLOW_STARTED = 'workflow_started'
    TASK_COMPLETED = 'task_completed'
    TASK_COMPLETED_V2 = 'task_completed_v2'  # Deprecated
    TASK_RETURNED = 'task_returned'

    VALUES = {
        WORKFLOW_COMPLETED,
        WORKFLOW_STARTED,
        TASK_COMPLETED,
        TASK_COMPLETED_V2,
        TASK_RETURNED
    }

    CHOICES = {
        WORKFLOW_COMPLETED: WORKFLOW_COMPLETED,
        WORKFLOW_STARTED: WORKFLOW_STARTED,
        TASK_COMPLETED: TASK_COMPLETED,
        TASK_COMPLETED_V2: TASK_COMPLETED_V2,
        TASK_RETURNED: TASK_RETURNED
    }

    LITERALS = Literal[
        WORKFLOW_COMPLETED,
        WORKFLOW_STARTED,
        TASK_COMPLETED,
        TASK_COMPLETED_V2,
        TASK_RETURNED,
    ]
