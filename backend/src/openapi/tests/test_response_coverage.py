"""Ensure public endpoints document their response body."""

import pytest
from drf_spectacular.generators import SchemaGenerator

pytestmark = pytest.mark.django_db

_METHODS_REQUIRING_BODY = frozenset({
    'get', 'post', 'put', 'patch',
})

_EMPTY_BODY_OPERATIONS = frozenset({
    # POST/PUT/PATCH actions that intentionally return
    # empty 200 (EMPTY response) — verified in code.

    # Accounts
    'accounts_users_delete_create',
    'accounts_users_toggle_admin_create',
    'accounts_users_reassign_create',

    # Auth
    'auth_reset_password_create',

    # Notifications
    'notifications_ios_reset_push_counter_create',

    # Templates
    'templates_clone_create',
    'templates_run_create',
    'templates_discard_create',
    'templates_discard_changes_create',
    'templates_presets_default_create',
    'templates_system_import_create',

    # Workflows
    'workflows_finish_create',
    'workflows_complete_create',
    'workflows_task_complete_create',
    'workflows_return_to_task_create',
    'workflows_return_to_create',
    'workflows_snooze_create',
    'workflows_resume_create',
    'workflows_remove_create',
    'workflows_comments_create_reaction_create',
    'workflows_comments_delete_reaction_create',
    'workflows_comments_watched_create',

    # Tasks
    'v2_tasks_complete_create',
    'v2_tasks_revert_create',
    'v2_tasks_create_performer_create',
    'v2_tasks_create_group_performer_create',
    'v2_tasks_delete_performer_create',
    'v2_tasks_delete_group_performer_create',
    'v2_tasks_delete_guest_performer_create',
    'v2_tasks_due_date_create',
    'v2_tasks_checklists_mark_create',
    'v2_tasks_checklists_unmark_create',

    # Datasets
    'datasets_create_items_create',
    'datasets_update_items_create',
    'datasets_delete_items_create',

    # Webhooks
    'webhooks_subscribe_create',
    'webhooks_unsubscribe_create',
    'webhooks_events_subscribe_create',
    'webhooks_events_unsubscribe_create',

    # Fieldsets
    'fieldsets_attach_create',
    'fieldsets_detach_create',
})

_DOCS_PREFIXES = (
    '/api/schema',
    '/api/docs',
    '/api/redoc',
)


def _is_docs_path(path: str) -> bool:
    normalized = path.rstrip('/')
    for prefix in _DOCS_PREFIXES:
        if (
            normalized == prefix
            or normalized.startswith(f'{prefix}/')
        ):
            return True
    return False


def _has_response_body(responses: dict) -> bool:
    """Check if at least one 2xx response has content."""
    for status, response in responses.items():
        if not status.startswith('2'):
            continue
        if not isinstance(response, dict):
            continue
        if response.get('content'):
            return True
    return False


def test_public_endpoints__response_body__ok():
    """Fail when a public GET/POST/PUT/PATCH endpoint
    has no response body documented.

    DELETE methods and explicitly whitelisted actions
    (intentional EMPTY responses) are skipped.
    """

    # arrange
    generator = SchemaGenerator()
    schema = generator.get_schema(
        request=None, public=True,
    )
    paths = schema.get('paths') or {}

    # act
    missing = []
    for path, operations in paths.items():
        if _is_docs_path(path):
            continue
        for method, operation in operations.items():
            if method not in _METHODS_REQUIRING_BODY:
                continue
            if not isinstance(operation, dict):
                continue
            op_id = operation.get('operationId', '')
            if op_id in _EMPTY_BODY_OPERATIONS:
                continue
            responses = operation.get('responses') or {}
            if not _has_response_body(responses):
                missing.append(
                    f'{method.upper()} {path} ({op_id})',
                )

    # assert
    assert missing == [], (
        'Endpoints without response body documented:\n'
        + '\n'.join(f'  - {m}' for m in missing)
    )
