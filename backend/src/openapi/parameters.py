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
    query_param('limit', OpenApiTypes.INT),
    query_param('offset', OpenApiTypes.INT),
]

DATE_RANGE_PARAMS = [
    query_param('date_from_tsp', OpenApiTypes.NUMBER),
    query_param('date_to_tsp', OpenApiTypes.NUMBER),
    query_param('now', OpenApiTypes.BOOL),
]

WORKFLOW_LIST_PARAMS = [
    query_param('status'),
    query_param('template_id'),
    query_param('template_task_api_name'),
    query_param('fields'),
    query_param('current_performer'),
    query_param('current_performer_group_ids'),
    query_param('workflow_starter'),
    query_param('ordering'),
    query_param('search'),
    query_param('is_external', OpenApiTypes.BOOL),
    *LIMIT_OFFSET_PARAMS,
]

WORKFLOW_FIELDS_PARAMS = [
    query_param('status'),
    query_param('template_id', OpenApiTypes.INT),
    query_param('fields'),
    *LIMIT_OFFSET_PARAMS,
]

WORKFLOW_EVENTS_PARAMS = [
    query_param('ordering'),
    query_param('include_comments', OpenApiTypes.BOOL),
    query_param('only_attachments', OpenApiTypes.BOOL),
    *LIMIT_OFFSET_PARAMS,
]

WEBHOOK_EXAMPLE_PARAMS = [
    query_param('status'),
    query_param('ordering'),
]

TASK_LIST_PARAMS = [
    query_param('is_completed', OpenApiTypes.BOOL),
    query_param('ordering'),
    query_param('assigned_to', OpenApiTypes.INT),
    query_param('search'),
    query_param('template_id', OpenApiTypes.INT),
    query_param('template_task_api_name'),
    *LIMIT_OFFSET_PARAMS,
]

COUNTS_BY_STARTER_PARAMS = [
    query_param('status'),
    query_param('template_ids'),
    query_param('current_performer_ids'),
    query_param('current_performer_group_ids'),
]

COUNTS_BY_PERFORMER_PARAMS = [
    query_param('is_external', OpenApiTypes.BOOL),
    query_param('template_ids'),
    query_param('template_task_api_names'),
    query_param('workflow_starter_ids'),
]

COUNTS_BY_TEMPLATE_TASK_PARAMS = [
    query_param('is_external', OpenApiTypes.BOOL),
    query_param('status'),
    query_param('template_ids'),
    query_param('workflow_starter_ids'),
    query_param('current_performer_ids'),
    query_param('current_performer_group_ids'),
]

CONTACTS_PARAMS = [
    query_param('ordering'),
    query_param('search'),
    query_param('source'),
    *LIMIT_OFFSET_PARAMS,
]

USERS_LIST_PARAMS = [
    query_param('status'),
    query_param('type'),
    query_param('ordering'),
    query_param('groups'),
    *LIMIT_OFFSET_PARAMS,
]

GROUPS_LIST_PARAMS = [
    query_param('ordering'),
]

BREAKDOWN_BY_STEPS_PARAMS = [
    *DATE_RANGE_PARAMS,
    query_param(
        'template_id',
        OpenApiTypes.INT,
        required=True,
    ),
]

HIGHLIGHTS_PARAMS = [
    query_param('templates'),
    query_param('current_performer_ids'),
    query_param('current_performer_group_ids'),
    query_param('date_before_tsp', OpenApiTypes.NUMBER),
    query_param('date_after_tsp', OpenApiTypes.NUMBER),
]

DATASETS_LIST_PARAMS = [
    query_param('ordering'),
    *LIMIT_OFFSET_PARAMS,
]

TEMPLATE_LIST_FILTER_PARAMS = [
    query_param('is_active', OpenApiTypes.BOOL),
    query_param('is_public', OpenApiTypes.BOOL),
    query_param('search'),
    query_param('ordering'),
]

TEMPLATE_EXPORT_PARAMS = [
    query_param('owners_ids'),
    query_param('owners_group_ids'),
    query_param('is_active', OpenApiTypes.BOOL),
    query_param('is_public', OpenApiTypes.BOOL),
    query_param('ordering'),
    *LIMIT_OFFSET_PARAMS,
]

TEMPLATE_TITLES_BY_WORKFLOWS_PARAMS = [
    query_param('status'),
]

TEMPLATE_TITLES_BY_EVENTS_PARAMS = [
    query_param('date_from_tsp', OpenApiTypes.NUMBER),
    query_param('date_to_tsp', OpenApiTypes.NUMBER),
]

TEMPLATE_TITLES_BY_TASKS_PARAMS = [
    query_param('status'),
]

TEMPLATE_STEPS_PARAMS = [
    query_param('with_tasks_in_progress', OpenApiTypes.BOOL),
]

TEMPLATE_INTEGRATIONS_PARAMS = [
    query_param('template_id'),
]

TEMPLATE_TITLES_BY_OWNERS_PARAMS = [
    *TEMPLATE_LIST_FILTER_PARAMS,
    *LIMIT_OFFSET_PARAMS,
]

RESET_PASSWORD_TOKEN_PARAMS = [
    query_param('token', required=True),
]

AI_DESCRIPTION_PARAMS = [
    query_param('description', required=True),
]
