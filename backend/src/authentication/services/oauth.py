from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Optional
from uuid import UUID

from django.db import transaction
from oauth2_provider.models import AbstractApplication, Application

from src.authentication.enums import (
    GrantType,
)
from src.authentication.exceptions import InvalidGrant
from src.mcp.models import (
    ClientPolicy,
    CodeBinding,
    Connection,
    RefreshBinding,
)
from src.authentication.services.connections import ConnectionService
from src.authentication.tokens import get_digest


class TokenExchangeService:
    @classmethod
    @contextmanager
    def lock_connection(cls, post_data: Mapping[str, str]) -> Iterator[None]:
        """Serialize a code exchange or refresh with group revocation."""
        connection_id = cls._get_connection_id(post_data=post_data)
        with transaction.atomic():
            connection = Connection.objects.filter(pk=connection_id).first()
            if connection is None:
                raise InvalidGrant
            ConnectionService.lock_group(connection=connection)
            yield

    @classmethod
    def _get_connection_id(
        cls,
        post_data: Mapping[str, str],
    ) -> Optional[UUID]:
        grant_type = post_data.get('grant_type')
        if grant_type == GrantType.AUTHORIZATION_CODE:
            bindings = CodeBinding.objects.filter(
                digest=get_digest(value=post_data.get('code', '')),
            )
        elif grant_type == GrantType.REFRESH_TOKEN:
            bindings = RefreshBinding.objects.filter(
                refresh_token__token_checksum=get_digest(
                    value=post_data.get('refresh_token', ''),
                ),
            )
        else:
            return None
        return bindings.values_list('connection_id', flat=True).first()


class ClientRegistrationService:
    """Dynamic client registration restricted to the MCP OAuth profile."""

    @classmethod
    def save_policy(cls, client_id: str) -> ClientPolicy:
        """Clients registered by anyone never get introspection rights."""
        policy, _created = ClientPolicy.objects.get_or_create(
            application=Application.objects.get(client_id=client_id),
            defaults={
                'registration_type': (
                    AbstractApplication.RegistrationSource.DCR
                ),
                'can_introspect': False,
            },
        )
        return policy
