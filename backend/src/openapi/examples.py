from drf_spectacular.utils import OpenApiExample


VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    'Validation error',
    value={
        'message': 'Template name cannot be empty',
        'code': 'validation_error',
        'details': {
            'name': 'name',
            'reason': 'Template name cannot be empty',
        },
    },
    response_only=True,
    status_codes=['400'],
)


def detail_example(
    name: str,
    detail: str,
    status_code: str,
) -> OpenApiExample:
    return OpenApiExample(
        name,
        value={'detail': detail},
        response_only=True,
        status_codes=[status_code],
    )


UNAUTHORIZED_EXAMPLE = detail_example(
    name='Unauthorized',
    detail=(
        'Authentication credentials were not provided.'
    ),
    status_code='401',
)
FORBIDDEN_EXAMPLE = detail_example(
    name='Forbidden',
    detail=(
        'You do not have permission to perform '
        'this action.'
    ),
    status_code='403',
)
NOT_FOUND_EXAMPLE = detail_example(
    name='Not found',
    detail='Not found.',
    status_code='404',
)
TOO_MANY_REQUESTS_EXAMPLE = detail_example(
    name='Too many requests',
    detail='Request was throttled.',
    status_code='429',
)


# -- Request examples (request_only) --------------------------------

TEMPLATE_CREATE_EXAMPLE = OpenApiExample(
    'Create active template',
    description=(
        'Replace owner and performer source_id with a user ID on your '
        'account. IDs are strings. Includes an empty kickoff form.'
    ),
    value={
        'name': 'Employee onboarding',
        'kickoff': {'fields': []},
        'owners': [{'type': 'user', 'role': 'owner', 'source_id': '1'}],
        'tasks': [
            {
                'name': 'Fill out paperwork',
                'number': 1,
                'raw_performers': [{'type': 'user', 'source_id': '1'}],
            },
        ],
        'is_active': True,
    },
    request_only=True,
)

TEMPLATE_DRAFT_EXAMPLE = OpenApiExample(
    'Create draft template',
    value={
        'name': 'Employee onboarding',
        'is_active': False,
        'description': 'Prepare a new employee for their first day.',
        'wf_name_template': 'Employee onboarding',
        'is_public': False,
        'is_embedded': False,
        'public_success_url': None,
        'finalizable': True,
        'reminder_notification': True,
        'completion_notification': False,
    },
    description=(
        'Inactive drafts accept incomplete data, including an empty object '
        'or a null name. An active template additionally requires kickoff '
        'and non-empty tasks and owners. Most draft settings are stored as '
        'supplied and validated only when activating the template. '
        'Public and embed flags are normalized to booleans.'
    ),
    request_only=True,
)

TEMPLATE_PREVIEW_EXAMPLE = OpenApiExample(
    'Unsaved template preview',
    description=(
        'Returned before saving. Generated api_name values vary. '
        'The owner source_id is a string; the default performer user ID '
        'is an integer.'
    ),
    value={
        'name': 'Employee onboarding',
        'wf_name_template': None,
        'description': '',
        'is_active': False,
        'finalizable': True,
        'is_public': False,
        'owners': [{'type': 'user', 'source_id': '1', 'role': 'owner'}],
        'kickoff': {
            'description': '',
            'fields': [{
                'name': 'Employee', 'type': 'text',
                'api_name': 'field-employee',
            }],
            'fieldsets': [{
                'title': 'Contact details',
                'api_name': 'contact-details',
                'fields': [{
                    'name': 'Phone', 'type': 'text',
                    'api_name': 'field-phone',
                }],
            }],
        },
        'tasks': [{
            'name': 'Fill out paperwork',
            'number': 1,
            'api_name': 'task-onboarding',
            'raw_performers': [{
                'type': 'user', 'source_id': 1, 'label': 'Jane Doe',
            }],
        }],
    },
    response_only=True,
    status_codes=['200'],
)


WORKFLOW_RUN_EXAMPLE = OpenApiExample(
    'Run workflow',
    value={
        'name': 'Onboard: Jane Doe',
        'is_urgent': False,
        'kickoff': {
            'employee-name': 'Jane Doe',
        },
    },
    request_only=True,
)

WORKFLOW_COMPLETE_EXAMPLE = OpenApiExample(
    'Complete current task',
    value={
        'task_id': 42,
        'output': {
            'result': 'Approved',
        },
    },
    request_only=True,
)

TASK_COMPLETE_EXAMPLE = OpenApiExample(
    'Complete task',
    value={
        'output': {
            'result': 'Done',
        },
    },
    request_only=True,
)

DATASET_CREATE_EXAMPLE = OpenApiExample(
    'Create dataset',
    value={
        'name': 'Departments',
        'description': 'Company departments list',
        'items': [
            {'value': 'Engineering', 'order': 0},
            {'value': 'Marketing', 'order': 1},
        ],
    },
    request_only=True,
)

WEBHOOK_SUBSCRIBE_EXAMPLE = OpenApiExample(
    'Subscribe to webhooks',
    value={
        'url': 'https://example.com/hooks/pneumatic',
    },
    request_only=True,
)

AI_PROVIDER_BY_VENDOR_EXAMPLE = OpenApiExample(
    'Create AI provider by vendor',
    value={
        'api_key': 'sk-or-v1-example',
        'vendor': 'openrouter',
    },
    request_only=True,
)

AI_PROVIDER_CREATE_EXAMPLE = OpenApiExample(
    'Create AI provider',
    value={
        'name': 'OpenRouter',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    },
    request_only=True,
)

AI_AGENT_CREATE_EXAMPLE = OpenApiExample(
    'Create AI agent',
    value={
        'name': 'Research assistant',
        'photo': 'https://example.com/images/assistant.jpg',
        'is_active': True,
        'provider_id': 1,
        'model': 'openai/gpt-4o',
        'system_prompt': 'You are a helpful research assistant.',
    },
    request_only=True,
)
