"""Reusable OpenAPI query parameters (docs only)."""

from typing import Optional

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter


def query_param(
    name: str,
    type_=OpenApiTypes.STR,
    required: bool = False,
    description: Optional[str] = None,
) -> OpenApiParameter:
    return OpenApiParameter(
        name=name,
        type=type_,
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
    )


LIMIT_OFFSET_PARAMS = [
    query_param(
        'limit', OpenApiTypes.INT,
        description='Maximum number of results to return.',
    ),
    query_param(
        'offset', OpenApiTypes.INT,
        description='Number of results to skip before returning.',
    ),
]

DATE_RANGE_PARAMS = [
    query_param(
        'date_from_tsp', OpenApiTypes.NUMBER,
        description='Start of date range (Unix timestamp).',
    ),
    query_param(
        'date_to_tsp', OpenApiTypes.NUMBER,
        description='End of date range (Unix timestamp).',
    ),
    query_param(
        'now', OpenApiTypes.BOOL,
        description=(
            'If true, use the current server time '
            'as the end of the date range.'
        ),
    ),
]

WORKFLOW_LIST_PARAMS = [
    query_param(
        'status',
        description=(
            'Filter by workflow status '
            '(running, delayed, completed, done).'
        ),
    ),
    query_param(
        'template_id',
        description='Filter by template ID.',
    ),
    query_param(
        'template_task_api_name',
        description=(
            'Filter by the API name of the current task step.'
        ),
    ),
    query_param(
        'fields',
        description=(
            'Comma-separated list of field API names '
            'to include in the response.'
        ),
    ),
    query_param(
        'current_performer',
        description='Filter by current performer user ID.',
    ),
    query_param(
        'current_performer_group_ids',
        description=(
            'Filter by current performer group IDs '
            '(comma-separated).'
        ),
    ),
    query_param(
        'workflow_starter',
        description='Filter by the user who started the workflow.',
    ),
    query_param(
        'ordering',
        description=(
            'Sort field. Prefix with "-" for descending '
            '(e.g. "-date_created").'
        ),
    ),
    query_param(
        'search',
        description='Full-text search across workflow names.',
    ),
    query_param(
        'is_external', OpenApiTypes.BOOL,
        description='Filter by external/internal workflows.',
    ),
    *LIMIT_OFFSET_PARAMS,
]

WORKFLOW_FIELDS_PARAMS = [
    query_param(
        'status',
        description='Filter by workflow status.',
    ),
    query_param(
        'template_id', OpenApiTypes.INT,
        description='Filter by template ID.',
    ),
    query_param(
        'fields',
        description=(
            'Comma-separated list of field API names '
            'to include.'
        ),
    ),
    *LIMIT_OFFSET_PARAMS,
]

WORKFLOW_EVENTS_PARAMS = [
    query_param(
        'ordering',
        description=(
            'Sort field. Prefix with "-" for descending.'
        ),
    ),
    query_param(
        'include_comments', OpenApiTypes.BOOL,
        description='Include comment events in the response.',
    ),
    query_param(
        'only_attachments', OpenApiTypes.BOOL,
        description='Return only events with attachments.',
    ),
    *LIMIT_OFFSET_PARAMS,
]

WEBHOOK_EXAMPLE_PARAMS = [
    query_param(
        'status',
        description='Filter example by workflow status.',
    ),
    query_param(
        'ordering',
        description='Sort field for the example list.',
    ),
]

TASK_LIST_PARAMS = [
    query_param(
        'is_completed', OpenApiTypes.BOOL,
        description=(
            'Filter by completion status '
            '(true = completed, false = active).'
        ),
    ),
    query_param(
        'ordering',
        description=(
            'Sort field. Prefix with "-" for descending '
            '(e.g. "-date_first_started").'
        ),
    ),
    query_param(
        'assigned_to', OpenApiTypes.INT,
        description='Filter by assigned performer user ID.',
    ),
    query_param(
        'search',
        description='Full-text search across task names.',
    ),
    query_param(
        'template_id', OpenApiTypes.INT,
        description='Filter by parent template ID.',
    ),
    query_param(
        'template_task_api_name',
        description='Filter by the task step API name.',
    ),
    *LIMIT_OFFSET_PARAMS,
]

COUNTS_BY_STARTER_PARAMS = [
    query_param(
        'status',
        description='Filter by workflow status.',
    ),
    query_param(
        'template_ids',
        description='Comma-separated template IDs to include.',
    ),
    query_param(
        'current_performer_ids',
        description=(
            'Comma-separated performer user IDs to filter by.'
        ),
    ),
    query_param(
        'current_performer_group_ids',
        description=(
            'Comma-separated performer group IDs to filter by.'
        ),
    ),
]

COUNTS_BY_PERFORMER_PARAMS = [
    query_param(
        'is_external', OpenApiTypes.BOOL,
        description='Filter by external/internal workflows.',
    ),
    query_param(
        'template_ids',
        description='Comma-separated template IDs to include.',
    ),
    query_param(
        'template_task_api_names',
        description=(
            'Comma-separated task step API names to filter by.'
        ),
    ),
    query_param(
        'workflow_starter_ids',
        description=(
            'Comma-separated user IDs of workflow starters.'
        ),
    ),
]

COUNTS_BY_TEMPLATE_TASK_PARAMS = [
    query_param(
        'is_external', OpenApiTypes.BOOL,
        description='Filter by external/internal workflows.',
    ),
    query_param(
        'status',
        description='Filter by workflow status.',
    ),
    query_param(
        'template_ids',
        description='Comma-separated template IDs to include.',
    ),
    query_param(
        'workflow_starter_ids',
        description=(
            'Comma-separated user IDs of workflow starters.'
        ),
    ),
    query_param(
        'current_performer_ids',
        description=(
            'Comma-separated performer user IDs to filter by.'
        ),
    ),
    query_param(
        'current_performer_group_ids',
        description=(
            'Comma-separated performer group IDs to filter by.'
        ),
    ),
]

CONTACTS_PARAMS = [
    query_param(
        'ordering',
        description='Sort field for contacts.',
    ),
    query_param(
        'search',
        description='Full-text search across contact names.',
    ),
    query_param(
        'source',
        description='Filter by contact source.',
    ),
    *LIMIT_OFFSET_PARAMS,
]

USERS_LIST_PARAMS = [
    query_param(
        'status',
        description=(
            'Filter by user status (active, inactive, invited).'
        ),
    ),
    query_param(
        'type',
        description='Filter by user type (user, guest).',
    ),
    query_param(
        'ordering',
        description=(
            'Sort field. Prefix with "-" for descending.'
        ),
    ),
    query_param(
        'groups',
        description=(
            'Comma-separated group IDs to filter users by.'
        ),
    ),
    *LIMIT_OFFSET_PARAMS,
]

GROUPS_LIST_PARAMS = [
    query_param(
        'ordering',
        description='Sort field for groups.',
    ),
]

BREAKDOWN_BY_STEPS_PARAMS = [
    *DATE_RANGE_PARAMS,
    query_param(
        'template_id',
        OpenApiTypes.INT,
        required=True,
        description='Template ID to break down by steps.',
    ),
]

HIGHLIGHTS_PARAMS = [
    query_param(
        'templates',
        description='Comma-separated template IDs to filter by.',
    ),
    query_param(
        'current_performer_ids',
        description=(
            'Comma-separated performer user IDs to filter by.'
        ),
    ),
    query_param(
        'current_performer_group_ids',
        description=(
            'Comma-separated performer group IDs to filter by.'
        ),
    ),
    query_param(
        'date_before_tsp', OpenApiTypes.NUMBER,
        description='Return highlights before this timestamp.',
    ),
    query_param(
        'date_after_tsp', OpenApiTypes.NUMBER,
        description='Return highlights after this timestamp.',
    ),
]

DATASETS_LIST_PARAMS = [
    query_param(
        'ordering',
        description='Sort field for datasets.',
    ),
    *LIMIT_OFFSET_PARAMS,
]

TEMPLATE_LIST_FILTER_PARAMS = [
    query_param(
        'is_active', OpenApiTypes.BOOL,
        description='Filter by active/inactive templates.',
    ),
    query_param(
        'is_public', OpenApiTypes.BOOL,
        description='Filter by public/private templates.',
    ),
    query_param(
        'search',
        description='Full-text search across template names.',
    ),
    query_param(
        'ordering',
        description=(
            'Sort field. Prefix with "-" for descending.'
        ),
    ),
]

TEMPLATE_EXPORT_PARAMS = [
    query_param(
        'owners_ids',
        description='Comma-separated owner user IDs to filter.',
    ),
    query_param(
        'owners_group_ids',
        description='Comma-separated owner group IDs to filter.',
    ),
    query_param(
        'is_active', OpenApiTypes.BOOL,
        description='Filter by active/inactive templates.',
    ),
    query_param(
        'is_public', OpenApiTypes.BOOL,
        description='Filter by public/private templates.',
    ),
    query_param(
        'ordering',
        description=(
            'Sort field. Prefix with "-" for descending.'
        ),
    ),
    *LIMIT_OFFSET_PARAMS,
]

TEMPLATE_TITLES_BY_WORKFLOWS_PARAMS = [
    query_param(
        'status',
        description='Filter by workflow status.',
    ),
]

TEMPLATE_TITLES_BY_EVENTS_PARAMS = [
    query_param(
        'date_from_tsp', OpenApiTypes.NUMBER,
        description='Start of date range (Unix timestamp).',
    ),
    query_param(
        'date_to_tsp', OpenApiTypes.NUMBER,
        description='End of date range (Unix timestamp).',
    ),
]

TEMPLATE_TITLES_BY_TASKS_PARAMS = [
    query_param(
        'status',
        description='Filter by task status.',
    ),
]

TEMPLATE_STEPS_PARAMS = [
    query_param(
        'with_tasks_in_progress', OpenApiTypes.BOOL,
        description=(
            'Only return steps that have tasks currently '
            'in progress.'
        ),
    ),
]

TEMPLATE_INTEGRATIONS_PARAMS = [
    query_param(
        'template_id',
        description='Filter integrations by template ID.',
    ),
]

TEMPLATE_TITLES_BY_OWNERS_PARAMS = [
    *TEMPLATE_LIST_FILTER_PARAMS,
    *LIMIT_OFFSET_PARAMS,
]

RESET_PASSWORD_TOKEN_PARAMS = [
    query_param(
        'token', required=True,
        description='Password reset token from the email link.',
    ),
]

AI_DESCRIPTION_PARAMS = [
    query_param(
        'description', required=True,
        description=(
            'Free-text workflow description for '
            'AI-powered step generation.'
        ),
    ),
]
