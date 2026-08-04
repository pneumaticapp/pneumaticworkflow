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
    'Create template (minimal)',
    value={
        'name': 'Employee onboarding',
        'tasks': [
            {
                'name': 'Fill out paperwork',
                'number': 1,
                'raw_performers': [{'type': 'user', 'source_id': 1}],
            },
        ],
        'is_active': True,
    },
    request_only=True,
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
