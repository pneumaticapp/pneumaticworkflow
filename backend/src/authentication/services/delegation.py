import src.authentication.messages as auth_messages
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.utils import timezone
from oauth2_provider.models import AccessToken
from rest_framework.exceptions import PermissionDenied

from src.authentication.constants import (
    DELEGATION_TOKEN_PREFIX,
    DELEGATION_TTL,
)
from src.authentication.exceptions import (
    InvalidMcpToken,
)
from src.mcp.models import AccessBinding, Connection, Delegation
from src.mcp.operations import get_operation
from src.authentication.services.connections import ConnectionService
from src.authentication.tokens import create_token, get_digest, get_expiration


@dataclass(frozen=True)
class IssuedDelegation:
    credential: str
    delegation: Delegation


class DelegationService:
    @classmethod
    def is_valid_source_token(
        cls,
        token: AccessToken,
        connection: Connection,
    ) -> bool:
        return (
            token.expires > timezone.now()
            and token.resource == [settings.MCP_PUBLIC_URL]
            and token.user_id == connection.user_id
            and token.application_id == connection.application_id
        )

    @classmethod
    def is_bound_token(
        cls,
        token: AccessToken,
        connection: Connection,
    ) -> bool:
        return AccessBinding.objects.filter(
            access_token=token,
            connection=connection,
        ).exists()

    @classmethod
    def get_access_binding(cls, token: str, resource: str) -> AccessBinding:
        if resource != settings.MCP_PUBLIC_URL:
            raise InvalidMcpToken
        binding = (
            AccessBinding.objects.select_related(
                'access_token',
                'connection__user__account',
                'connection__account',
                'connection__application',
            )
            .filter(access_token__token_checksum=get_digest(value=token))
            .first()
        )
        if binding is None or not cls._is_active_binding(binding=binding):
            raise InvalidMcpToken
        return binding

    @classmethod
    def create(
        cls,
        token: str,
        resource: str,
        tool: str,
        method: str,
        path: str,
        scopes: Optional[list[str]] = None,
    ) -> IssuedDelegation:
        """Exchange an access token for a one-request credential.

        The credential is bound to a single operation: method, path and
        audience. It narrows the token scopes and never outlives it.
        """
        binding = cls.get_access_binding(token=token, resource=resource)
        operation = get_operation(tool=tool, method=method, path=path)
        if operation is None:
            raise PermissionDenied
        granted = set(binding.access_token.scope.split())
        requested = granted if scopes is None else set(scopes)
        if not operation.required_scopes <= requested <= granted:
            raise PermissionDenied
        credential = create_token(prefix=DELEGATION_TOKEN_PREFIX)
        delegation = Delegation.objects.create(
            digest=get_digest(value=credential),
            connection=binding.connection,
            source_token=binding.access_token,
            audience=operation.audience,
            operation=tool,
            method=method,
            path=path,
            scopes=sorted(requested),
            expires_at=get_expiration(
                ttl=DELEGATION_TTL,
                limit=binding.access_token.expires,
            ),
        )
        return IssuedDelegation(credential=credential, delegation=delegation)

    @classmethod
    def get_delegation(cls, credential: str) -> Delegation:
        delegation = (
            Delegation.objects.select_related(
                'connection__user__account',
                'connection__account',
                'connection__application',
                'source_token',
            )
            .filter(digest=get_digest(value=credential))
            .first()
        )
        if delegation is None or not cls._is_active_delegation(
            delegation=delegation,
        ):
            raise InvalidMcpToken(auth_messages.MSG_AU_0028)
        return delegation

    @classmethod
    def _is_active_binding(cls, binding: AccessBinding) -> bool:
        access = binding.access_token
        connection = binding.connection
        return (
            cls.is_valid_source_token(token=access, connection=connection)
            and set(access.scope.split()) <= set(connection.scopes)
            and ConnectionService.is_live(connection=connection)
        )

    @classmethod
    def _is_active_delegation(cls, delegation: Delegation) -> bool:
        operation = get_operation(
            tool=delegation.operation,
            method=delegation.method,
            path=delegation.path,
        )
        source = delegation.source_token
        connection = delegation.connection
        scopes = set(delegation.scopes)
        return (
            operation is not None
            and delegation.audience == operation.audience
            and delegation.expires_at > timezone.now()
            and cls.is_valid_source_token(token=source, connection=connection)
            and scopes <= set(source.scope.split())
            and scopes <= set(connection.scopes)
            and operation.required_scopes <= scopes
            and ConnectionService.is_live(connection=connection)
            and cls.is_bound_token(token=source, connection=connection)
        )
