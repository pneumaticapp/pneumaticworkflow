import src.authentication.messages as auth_messages
from typing import Optional

from django.utils.functional import Promise
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
)

from src.authentication.enums import (
    OAuthErrorCode,
)


class AuthorizationRequestGone(APIException):
    status_code = 410
    default_detail = auth_messages.MSG_AU_0022


class InvalidMcpToken(AuthenticationFailed):
    """The MCP server re-authenticates the user on `invalid_token`."""

    def __init__(self, message: str | Promise = auth_messages.MSG_AU_0023):
        super().__init__(
            detail={
                'detail': message,
                'code': OAuthErrorCode.INVALID_TOKEN,
            },
        )


class ServiceAuthenticationFailed(AuthenticationFailed):
    def __init__(self, message: str | Promise):
        super().__init__(
            detail={
                'detail': message,
                'code': OAuthErrorCode.SERVICE_AUTH_FAILED,
            },
        )


class InsufficientScope(PermissionDenied):
    """The MCP server asks the user to grant `required_scopes`."""

    def __init__(self, required_scopes: Optional[list[str]] = None):
        super().__init__(
            detail={
                'detail': PermissionDenied.default_detail,
                'code': OAuthErrorCode.INSUFFICIENT_SCOPE,
                'required_scopes': required_scopes or [],
            },
        )


class InvalidLoginCode(Exception):
    pass


class InvalidGrant(Exception):
    """Unknown authorization code or refresh token at the token endpoint."""


class InvalidClientMetadata(Exception):
    """Client metadata outside the MCP OAuth profile."""


class InactiveGrant(Exception):
    """Storage gets `{'active': false}` without the reason."""
