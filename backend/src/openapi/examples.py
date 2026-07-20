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
