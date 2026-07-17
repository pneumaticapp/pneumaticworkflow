"""OpenAPI helpers for drf-spectacular (docs only)."""

# Registers OpenApiAuthenticationExtension subclasses.
from src.openapi import auth_extensions as _auth_extensions  # noqa: F401
from src.openapi.entities import PermissionDoc
from src.openapi.helpers import (
    LIMIT_OFFSET_LEGACY_NOTE,
    access_description,
    with_access_text,
)
from src.openapi.permission_docs import (
    ACCESS_ACCOUNT_OWNER,
    ACCESS_ADMIN,
    ACCESS_ATTACHMENT,
    ACCESS_AUTH,
    ACCESS_AUTH_OVERLIMIT,
    ACCESS_PRESET,
    ACCESS_PUBLIC_TEMPLATE,
    ACCESS_STAFF_IMPORT,
    ACCESS_SYSTEM_TEMPLATE,
    ACCESS_TEMPLATE_ACCESS,
    ACCESS_TEMPLATE_AI,
    ACCESS_TEMPLATE_FIELDS,
    ACCESS_TEMPLATE_OWNER,
)
from src.openapi.responses import (
    EMPTY,
    FORBIDDEN,
    NOT_FOUND,
    TOO_MANY_REQUESTS,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    DetailErrorSerializer,
    ValidationErrorSerializer,
)

__all__ = (
    'ACCESS_ACCOUNT_OWNER',
    'ACCESS_ADMIN',
    'ACCESS_ATTACHMENT',
    'ACCESS_AUTH',
    'ACCESS_AUTH_OVERLIMIT',
    'ACCESS_PRESET',
    'ACCESS_PUBLIC_TEMPLATE',
    'ACCESS_STAFF_IMPORT',
    'ACCESS_SYSTEM_TEMPLATE',
    'ACCESS_TEMPLATE_ACCESS',
    'ACCESS_TEMPLATE_AI',
    'ACCESS_TEMPLATE_FIELDS',
    'ACCESS_TEMPLATE_OWNER',
    'EMPTY',
    'FORBIDDEN',
    'LIMIT_OFFSET_LEGACY_NOTE',
    'NOT_FOUND',
    'TOO_MANY_REQUESTS',
    'UNAUTHORIZED',
    'VALIDATION_ERROR',
    'DetailErrorSerializer',
    'PermissionDoc',
    'ValidationErrorSerializer',
    'access_description',
    'with_access_text',
)
