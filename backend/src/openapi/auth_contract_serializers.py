"""Schema-only contracts for authentication endpoints."""


OKTA_LOGOUT_REQUEST_SCHEMA = {
    'oneOf': [
        {'type': 'object', 'additionalProperties': True},
        {'type': 'array', 'items': {}},
        {'type': 'string'},
        {'type': 'number'},
        {'type': 'boolean'},
    ],
}
