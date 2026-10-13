import src.authentication.messages as auth_messages
import secrets
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.request import Request

from src.authentication.enums import AuthTokenType
from src.authentication.services.delegation import DelegationService
from src.authentication.services.user_auth import PneumaticTokenAuthentication
from src.authentication.tokens import PneumaticToken
from src.authentication.constants import (
    DELEGATION_TOKEN_PREFIX,
    FILE_SERVICE_SECRET_HEADER,
    MCP_TOKEN_MARKER,
    SERVICE_SECRET_HEADER,
)
from src.mcp.enums import McpAudience
from src.authentication.exceptions import (
    ServiceAuthenticationFailed,
)
from src.mcp.models import Delegation
from src.authentication.services.connections import ConnectionService


class BaseSecretAuthentication(BaseAuthentication):
    """Private service-to-service calls signed with a shared secret.

    The two secrets must differ so that one service cannot act as the
    other one.
    """

    header: str
    scheme: str
    message: str
    auth: str

    def authenticate(self, request: Request | HttpRequest):
        expected = self._get_secret()
        supplied = self._get_supplied_secret(request=request)
        if (
            not expected
            or expected == self._get_other_secret()
            or not secrets.compare_digest(
                supplied.encode('utf-8'),
                expected.encode('utf-8'),
            )
        ):
            raise ServiceAuthenticationFailed(self.message)
        return AnonymousUser(), self.auth

    def authenticate_header(self, request: Request | HttpRequest) -> str:
        return self.scheme

    def _get_supplied_secret(self, request: Request | HttpRequest) -> str:
        return request.headers.get(self.header, '')

    def _get_secret(self) -> str:
        raise NotImplementedError

    def _get_other_secret(self) -> str:
        raise NotImplementedError


class ServiceAuthentication(BaseSecretAuthentication):
    """The MCP server introspects tokens and requests delegations."""

    header = SERVICE_SECRET_HEADER
    scheme = 'MCP-Service'
    message = auth_messages.MSG_AU_0024
    auth = 'mcp-service'

    def _get_secret(self) -> str:
        return settings.MCP_SERVICE_SECRET

    def _get_other_secret(self) -> str:
        return settings.MCP_FILE_SERVICE_SECRET


class StorageAuthentication(BaseSecretAuthentication):
    """The file service validates MCP credentials and completes uploads."""

    header = FILE_SERVICE_SECRET_HEADER
    scheme = 'MCP-Storage'
    message = auth_messages.MSG_AU_0025
    auth = 'mcp-storage'

    def _get_supplied_secret(self, request: Request | HttpRequest) -> str:
        supplied = super()._get_supplied_secret(request=request)
        if supplied:
            return supplied
        parts = request.headers.get('Authorization', '').split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
        return ''

    def _get_secret(self) -> str:
        return settings.MCP_FILE_SERVICE_SECRET

    def _get_other_secret(self) -> str:
        return settings.MCP_SERVICE_SECRET


class LoginTokenAuthentication(PneumaticTokenAuthentication):
    """Only a browser login of an active user may manage MCP consent."""

    def authenticate_credentials(self, token: str):
        data = PneumaticToken.data(token=token)
        if not data or data['for_api_key'] or data['is_superuser']:
            raise AuthenticationFailed(auth_messages.MSG_AU_0026)
        result = super().authenticate_credentials(token=token)
        if result is None:
            raise AuthenticationFailed(auth_messages.MSG_AU_0030)
        user, _token = result
        if not ConnectionService.is_eligible_user(
            user=user,
            account_id=data['account_id'],
        ):
            raise AuthenticationFailed(auth_messages.MSG_AU_0027)
        return result


class DelegationAuthentication(BaseAuthentication):
    """One-request credentials the MCP server sends on behalf of a user."""

    def authenticate(
        self,
        request: Request | HttpRequest,
    ) -> Optional[tuple]:
        parts = request.headers.get('Authorization', '').split()
        if len(parts) != 2 or not parts[1].startswith(MCP_TOKEN_MARKER):
            return None
        if parts[0].lower() != 'bearer' or not parts[1].startswith(
            DELEGATION_TOKEN_PREFIX,
        ):
            raise AuthenticationFailed(auth_messages.MSG_AU_0031)
        delegation = DelegationService.get_delegation(credential=parts[1])
        self._check_request(request=request, delegation=delegation)
        request.token_type = AuthTokenType.API
        request.is_superuser = False
        request.session['is_authenticated'] = True
        return delegation.connection.user, delegation

    def authenticate_header(self, request: Request | HttpRequest) -> str:
        return 'Bearer'

    def _check_request(
        self,
        request: Request | HttpRequest,
        delegation: Delegation,
    ):
        if (
            delegation.audience != McpAudience.BACKEND
            or delegation.method != request.method
            or delegation.path != request.path
        ):
            raise PermissionDenied
