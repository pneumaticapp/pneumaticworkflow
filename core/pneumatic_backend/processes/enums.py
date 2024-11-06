from typing_extensions import Literal


class WorkflowStatus:

    RUNNING = 0
    DONE = 1
    DELAYED = 3

    CHOICES = (
        (RUNNING, 'Workflow in work'),
        (DONE, 'Workflow done'),
        (DELAYED, 'Workflow delayed'),
    )
    END_STATUSES = {DONE}
    RUNNING_STATUSES = {RUNNING, DELAYED}


class WorkflowApiStatus:

    RUNNING = 'running'
    DONE = 'done'
    DELAYED = 'snoozed'

    NOT_RUNNING = {DONE, DELAYED}

    CHOICES = (
        (RUNNING, 'Workflow in work'),
        (DONE, 'Workflow done'),
        (DELAYED, 'Workflow snoozed'),
    )
    MAP = {
        RUNNING: WorkflowStatus.RUNNING,
        DONE: WorkflowStatus.DONE,
        DELAYED: WorkflowStatus.DELAYED,
    }


class WorkflowOrdering:

    URGENT_FIRST = '-urgent'
    OVERDUE_FIRST = 'overdue'
    NEWEST_FIRST = '-date'
    OLDEST_FIRST = 'date'

    CHOICES = (
        (URGENT_FIRST, 'urgent first'),
        (OVERDUE_FIRST, 'overdue first'),
        (NEWEST_FIRST, 'newest first'),
        (OLDEST_FIRST, 'oldest first'),
    )

    MAP = {
        URGENT_FIRST: 'workflows.is_urgent',
        OVERDUE_FIRST: 'workflows.nearest_due_date',
        NEWEST_FIRST: 'workflows.date_created',
        OLDEST_FIRST: 'workflows.date_created',
    }

    LITERALS = Literal[
        URGENT_FIRST,
        OVERDUE_FIRST,
        NEWEST_FIRST,
        OLDEST_FIRST,
    ]


class PerformerType:

    USER = 'user'
    GROUP = 'group'
    WORKFLOW_STARTER = 'workflow_starter'
    FIELD = 'field'

    choices = (
        (USER, USER),
        (GROUP, GROUP),
        (WORKFLOW_STARTER, WORKFLOW_STARTER),
        (FIELD, FIELD)
    )


class DirectlyStatus:

    NO_STATUS = 0
    DELETED = 1
    CREATED = 2

    CHOICES = (
        (NO_STATUS, 'no status'),
        (DELETED, 'deleted'),
        (CREATED, 'created'),
    )


class CommentStatus:

    CREATED = 'created'
    UPDATED = 'updated'
    DELETED = 'deleted'

    CHOICES = (
        (CREATED, CREATED),
        (UPDATED, UPDATED),
        (DELETED, DELETED),
    )


class FieldType:

    STRING = 'string'
    TEXT = 'text'
    RADIO = 'radio'
    CHECKBOX = 'checkbox'
    DATE = 'date'
    URL = 'url'
    DROPDOWN = 'dropdown'
    FILE = 'file'
    USER = 'user'

    TYPES_WITH_SELECTIONS = {
        DROPDOWN,
        CHECKBOX,
        RADIO
    }
    TYPES_WITH_SELECTION = {
        DROPDOWN,
        RADIO
    }
    CHOICES = (
        (STRING, 'String'),
        (TEXT, 'Text'),
        (RADIO, 'Radio'),
        (CHECKBOX, 'Checkbox'),
        (DATE, 'Date'),
        (URL, 'Url'),
        (DROPDOWN, 'Dropdown'),
        (FILE, 'File'),
        (USER, 'User')
    )

    LITERALS = Literal[
        STRING,
        TEXT,
        RADIO,
        CHECKBOX,
        DATE,
        URL,
        DROPDOWN,
        FILE,
        USER,
    ]


class PredicateType:

    KICKOFF = 'kickoff'
    TASK = 'task'

    # Field types
    STRING = 'string'
    TEXT = 'text'
    RADIO = 'radio'
    CHECKBOX = 'checkbox'
    DATE = 'date'
    URL = 'url'
    DROPDOWN = 'dropdown'
    FILE = 'file'
    USER = 'user'

    CHOICES = (
        (KICKOFF, KICKOFF),
        (TASK, TASK),
        (STRING, STRING),
        (TEXT, TEXT),
        (RADIO, RADIO),
        (CHECKBOX, CHECKBOX),
        (DATE, DATE),
        (URL, URL),
        (DROPDOWN, DROPDOWN),
        (FILE, FILE),
        (USER, USER)
    )

    FIELD_TYPES = {
        STRING,
        TEXT,
        RADIO,
        CHECKBOX,
        DATE,
        URL,
        DROPDOWN,
        FILE,
        USER,
    }


class PredicateOperator:

    EQUAL = 'equals'
    NOT_EQUAL = 'not_equals'
    EXIST = 'exists'
    NOT_EXIST = 'not_exists'
    CONTAIN = 'contains'
    NOT_CONTAIN = 'not_contains'
    MORE_THAN = 'more_than'
    LESS_THAN = 'less_than'
    COMPLETED = 'completed'
    CHOICES = (
        (EQUAL, 'Equal'),
        (NOT_EQUAL, 'Not equal'),
        (EXIST, 'Exists'),
        (NOT_EXIST, 'Not exists'),
        (CONTAIN, 'Contains'),
        (NOT_CONTAIN, 'Not contains'),
        (MORE_THAN, 'More than'),
        (LESS_THAN, 'Less than'),
        (COMPLETED, COMPLETED),
    )
    ALLOWED_OPERATORS = {
        PredicateType.KICKOFF: {COMPLETED},
        PredicateType.TASK: {COMPLETED},
        PredicateType.USER: {EQUAL, NOT_EQUAL, EXIST, NOT_EXIST},
        PredicateType.FILE: {EXIST, NOT_EXIST},
        PredicateType.URL: {
            EQUAL,
            NOT_EQUAL,
            CONTAIN,
            NOT_CONTAIN,
            EXIST,
            NOT_EXIST,
        },
        PredicateType.DATE: {
            EQUAL,
            NOT_EQUAL,
            MORE_THAN,
            LESS_THAN,
            EXIST,
            NOT_EXIST,
        },
        PredicateType.CHECKBOX: {
            EQUAL,
            NOT_EQUAL,
            CONTAIN,
            NOT_CONTAIN,
            EXIST,
            NOT_EXIST,
        },
        PredicateType.STRING: {
            EQUAL,
            NOT_EQUAL,
            CONTAIN,
            NOT_CONTAIN,
            EXIST,
            NOT_EXIST,
        },
        PredicateType.DROPDOWN: {EQUAL, NOT_EQUAL, EXIST, NOT_EXIST},
        PredicateType.RADIO: {EQUAL, NOT_EQUAL, EXIST, NOT_EXIST},
        PredicateType.TEXT: {
            EQUAL,
            NOT_EQUAL,
            CONTAIN,
            NOT_CONTAIN,
            EXIST,
            NOT_EXIST,
        },
    }
    UNARY_OPERATORS = {EXIST, NOT_EXIST, COMPLETED}


class TemplateOrdering:

    NAME = 'name'
    REVERSE_NAME = '-name'
    DATE = 'date'
    REVERSE_DATE = '-date'
    USAGE = 'usage'
    REVERSE_USAGE = '-usage'

    VALUES = {NAME, REVERSE_NAME, DATE, REVERSE_DATE, USAGE, REVERSE_USAGE}
    CHOICES = (
        (NAME, NAME),
        (REVERSE_NAME, REVERSE_NAME),
        (DATE, DATE),
        (REVERSE_DATE, REVERSE_DATE),
        (USAGE, USAGE),
        (REVERSE_USAGE, REVERSE_USAGE),
    )
    MAP = {
        NAME: 'templates.name',
        REVERSE_NAME: 'templates.name',
        DATE: 'templates.date_created',
        REVERSE_DATE: 'templates.date_created',
        USAGE: 'templates.workflows_count',
        REVERSE_USAGE: 'templates.workflows_count',
    }


class TaskOrdering:

    DATE_STARTED = 'date'
    DATE_STARTED_REVERSED = '-date'
    END_DATE = 'overdue'
    END_DATE_REVERSED = '-overdue'
    DATE_COMPLETED = 'completed'
    DATE_COMPLETED_REVERSED = '-completed'

    CHOICES = (
        (DATE_STARTED, DATE_STARTED),
        (DATE_STARTED_REVERSED, DATE_STARTED_REVERSED),
        (END_DATE, END_DATE),
        (END_DATE_REVERSED, END_DATE_REVERSED),
        (DATE_COMPLETED, DATE_COMPLETED),
        (DATE_COMPLETED_REVERSED, DATE_COMPLETED_REVERSED),
    )

    MAP = {
        DATE_STARTED: 'tasks.date_started',
        DATE_STARTED_REVERSED: 'tasks.date_started',
        END_DATE: 'tasks.due_date',
        END_DATE_REVERSED: 'tasks.due_date',
        DATE_COMPLETED: 'tasks.date_completed',
        DATE_COMPLETED_REVERSED: 'tasks.date_completed',
    }


class TemplateIntegrationType:

    SHARED = 'shared'
    ZAPIER = 'zapier'
    API = 'api'
    WEBHOOKS = 'webhooks'

    LITERALS = Literal[
        'shared',
        'zapier',
        'api',
        'webhooks'
    ]


class TemplateType:

    CUSTOM = 'user'
    LIBRARY = 'from_library'
    ONBOARDING_ADMIN = 'builtin_admin_onboarding'
    ONBOARDING_NON_ADMIN = 'builtin_user_onboarding'
    ONBOARDING_ACCOUNT_OWNER = 'builtin_account_owner_onboarding'

    CHOICES = (
        (CUSTOM, 'custom'),
        (LIBRARY, 'library'),
        (ONBOARDING_ADMIN, 'Onboarding admin user'),
        (ONBOARDING_NON_ADMIN, 'Onboarding not admin user'),
        (ONBOARDING_ACCOUNT_OWNER, 'Onboarding account owner'),
    )

    TYPES_ONBOARDING = {
        ONBOARDING_ADMIN,
        ONBOARDING_NON_ADMIN,
        ONBOARDING_ACCOUNT_OWNER
    }

    USER_TYPES = {
        LIBRARY,
        CUSTOM
    }


class SysTemplateType:

    LIBRARY = 'generic'
    ACTIVATED = 'activated_template'
    ONBOARDING_ACCOUNT_OWNER = 'owner_onboarding'
    ONBOARDING_ADMIN = 'invited_onboarding_admin'
    ONBOARDING_NON_ADMIN = 'invited_onboarding_regular'

    CHOICES = (
        (LIBRARY, 'Library'),
        (ONBOARDING_ACCOUNT_OWNER, 'Onboarding account owners'),
        (ONBOARDING_ADMIN, 'Onboarding admin users'),
        (ONBOARDING_NON_ADMIN, 'Onboarding non-admin users'),
        (ACTIVATED, 'Activated')
    )

    ONBOARDING_CHOICES = (
        (ONBOARDING_ACCOUNT_OWNER, 'Onboarding account owners'),
        (ONBOARDING_ADMIN, 'Onboarding admin users'),
        (ONBOARDING_NON_ADMIN, 'Onboarding non-admin users'),
    )

    TYPES_ONBOARDING = {
        ONBOARDING_ACCOUNT_OWNER,
        ONBOARDING_ADMIN,
        ONBOARDING_NON_ADMIN
    }

    TYPES_ONBOARDING_AND_ACTIVATED = {
        ONBOARDING_ACCOUNT_OWNER,
        ONBOARDING_ADMIN,
        ONBOARDING_NON_ADMIN,
        ACTIVATED,
    }


sys_template_type_map = {
    SysTemplateType.LIBRARY: TemplateType.LIBRARY,
    SysTemplateType.ACTIVATED: TemplateType.CUSTOM,
    SysTemplateType.ONBOARDING_ACCOUNT_OWNER: (
        TemplateType.ONBOARDING_ACCOUNT_OWNER
    ),
    SysTemplateType.ONBOARDING_ADMIN: (
        TemplateType.ONBOARDING_ADMIN
    ),
    SysTemplateType.ONBOARDING_NON_ADMIN: (
        TemplateType.ONBOARDING_NON_ADMIN
    ),
}


class DueDateRule:

    BEFORE_FIELD = 'before field'
    AFTER_FIELD = 'after field'
    AFTER_WORKFLOW_STARTED = 'after workflow started'
    AFTER_TASK_STARTED = 'after task started'
    AFTER_TASK_COMPLETED = 'after task completed'

    TASK_RULES = {
        AFTER_TASK_STARTED,
        AFTER_TASK_COMPLETED
    }

    FIELD_RULES = {
        AFTER_FIELD,
        BEFORE_FIELD
    }

    LITERALS = Literal[
        BEFORE_FIELD,
        AFTER_FIELD,
        AFTER_WORKFLOW_STARTED,
        AFTER_TASK_STARTED,
        AFTER_TASK_COMPLETED,
    ]
    CHOICES = (
        (BEFORE_FIELD, BEFORE_FIELD),
        (AFTER_FIELD, AFTER_FIELD),
        (AFTER_WORKFLOW_STARTED, AFTER_WORKFLOW_STARTED),
        (AFTER_TASK_STARTED, AFTER_TASK_STARTED),
        (AFTER_TASK_COMPLETED, AFTER_TASK_COMPLETED),
    )


class WorkflowEventType:

    # Workflow events
    RUN = 0
    COMPLETE = 1
    ENDED = 6
    DELAY = 7
    ENDED_BY_CONDITION = 10
    URGENT = 11
    NOT_URGENT = 12
    FORCE_RESUME = 16
    FORCE_DELAY = 17

    # Task events
    TASK_START = 2
    TASK_COMPLETE = 3
    TASK_REVERT = 4
    COMMENT = 5
    REVERT = 8
    TASK_SKIP = 9
    TASK_SKIP_NO_PERFORMERS = 13
    TASK_PERFORMER_CREATED = 14
    TASK_PERFORMER_DELETED = 15
    DUE_DATE_CHANGED = 18
    SUB_WORKFLOW_RUN = 19

    URGENT_TYPES = (
        URGENT,
        NOT_URGENT
    )

    CHOICES = (
        (RUN, 'Workflow started'),
        (COMPLETE, 'Workflow completed'),
        (TASK_START, 'Task started'),
        (TASK_COMPLETE, 'Task completed'),
        (TASK_REVERT, 'Task reverted'),
        (TASK_SKIP, 'Task skipped'),
        (COMMENT, 'New comment'),
        (ENDED, 'Workflow ended'),
        (DELAY, 'Workflow snoozed from template'),
        (FORCE_DELAY, 'Workflow snoozed'),
        (REVERT, 'Workflow reverted'),
        (ENDED_BY_CONDITION, 'Workflow ended by condition'),
        (URGENT, 'Workflow is urgent'),
        (NOT_URGENT, 'Workflow is not urgent'),
        (
            TASK_SKIP_NO_PERFORMERS,
            'Task skipped as no performers were assigned'
        ),
        (TASK_PERFORMER_CREATED, 'Performer added to task'),
        (TASK_PERFORMER_DELETED, 'Performer deleted from task'),
        (FORCE_RESUME, 'Workflow resumed'),
        (DUE_DATE_CHANGED, 'Due date changed'),
    )


class WorkflowEventActionType:

    WATCHED = 0

    CHOICES = (
        (WATCHED, 'Watched'),
    )
