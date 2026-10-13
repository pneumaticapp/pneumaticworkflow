from typing import Any, Optional

from django.db import transaction
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application, RefreshToken
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauthlib.common import Request as OAuthRequest

from src.authentication.constants import (
    CODE_BINDING_TTL,
)
from src.authentication.enums import (
    GrantType,
)
from src.mcp.models import (
    AccessBinding,
    ClientPolicy,
    CodeBinding,
    RefreshBinding,
)
from src.authentication.services.connections import ConnectionService
from src.authentication.tokens import get_digest


class MCPValidator(OAuth2Validator):
    """Bind every code and token to the consent it was issued for.

    The binding lets revocation of one consent revoke all its tokens and
    keeps refresh tokens of a revoked consent from being reused.
    """

    RESPONSE_TYPE = 'code'

    def _load_application(
        self,
        client_id: str,
        request: OAuthRequest,
    ) -> Optional[Application]:
        client = super()._load_application(client_id, request)
        if client is None:
            return None
        policy, _created = ClientPolicy.objects.get_or_create(
            application=client,
            defaults={'registration_type': client.registration_source},
        )
        if not policy.is_active:
            request.client = None
            return None
        return client

    def validate_response_type(
        self,
        client_id: str,
        response_type: str,
        client: Application,
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        return response_type == self.RESPONSE_TYPE and (
            super().validate_response_type(
                client_id,
                response_type,
                client,
                request,
                *args,
                **kwargs,
            )
        )

    def validate_grant_type(
        self,
        client_id: str,
        grant_type: str,
        client: Application,
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        return grant_type in GrantType.ALLOWED and (
            super().validate_grant_type(
                client_id,
                grant_type,
                client,
                request,
                *args,
                **kwargs,
            )
        )

    @transaction.atomic
    def save_authorization_code(
        self,
        client_id: str,
        code: dict,
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ):
        super().save_authorization_code(
            client_id,
            code,
            request,
            *args,
            **kwargs,
        )
        connection = ConnectionService.save_grant(
            user=request.user,
            application=request.client,
            scopes=request.scopes,
        )
        CodeBinding.objects.create(
            digest=get_digest(value=code['code']),
            connection=connection,
            expires_at=timezone.now() + CODE_BINDING_TTL,
        )

    def validate_code(
        self,
        client_id: str,
        code: str,
        client: Application,
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        binding = (
            CodeBinding.objects.select_related(
                'connection__user__account',
                'connection__account',
            )
            .filter(digest=get_digest(value=code))
            .first()
        )
        if (
            binding is None
            or binding.expires_at <= timezone.now()
            or binding.connection.application_id != client.pk
            or not ConnectionService.is_live(connection=binding.connection)
        ):
            return False
        request.mcp_connection = binding.connection
        return super().validate_code(
            client_id,
            code,
            client,
            request,
            *args,
            **kwargs,
        )

    def validate_refresh_token(
        self,
        refresh_token: str,
        client: Application,
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        binding = (
            RefreshBinding.objects.select_related(
                'refresh_token',
                'connection__user__account',
                'connection__account',
            )
            .filter(
                refresh_token__token_checksum=get_digest(
                    value=refresh_token,
                ),
            )
            .first()
        )
        if (
            binding is None
            or binding.connection.application_id != client.pk
            or not ConnectionService.is_live(connection=binding.connection)
        ):
            return False
        is_valid = super().validate_refresh_token(
            refresh_token,
            client,
            request,
            *args,
            **kwargs,
        )
        if not is_valid:
            if binding.refresh_token.revoked:
                # A rotated token was replayed: treat the consent as leaked.
                ConnectionService.revoke(connection=binding.connection)
            return False
        request.mcp_connection = binding.connection
        return True

    def _save_bearer_token(
        self,
        token: dict,
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ):
        super()._save_bearer_token(token, request, *args, **kwargs)
        AccessBinding.objects.create(
            access_token=AccessToken.objects.get(
                token_checksum=get_digest(value=token['access_token']),
            ),
            connection=request.mcp_connection,
        )
        if 'refresh_token' in token:
            RefreshBinding.objects.get_or_create(
                refresh_token=RefreshToken.objects.get(
                    token_checksum=get_digest(value=token['refresh_token']),
                ),
                defaults={'connection': request.mcp_connection},
            )
        if request.grant_type == GrantType.AUTHORIZATION_CODE:
            CodeBinding.objects.filter(
                digest=get_digest(value=request.code),
            ).delete()

    def revoke_token(
        self,
        token: str,
        token_type_hint: Optional[str],
        request: OAuthRequest,
        *args: Any,
        **kwargs: Any,
    ):
        binding = (
            AccessBinding.objects.filter(
                access_token__token_checksum=get_digest(value=token),
                access_token__application=request.client,
            ).first()
            or RefreshBinding.objects.filter(
                refresh_token__token_checksum=get_digest(value=token),
                refresh_token__application=request.client,
            ).first()
        )
        if binding is not None:
            ConnectionService.revoke(connection=binding.connection)
        super().revoke_token(token, token_type_hint, request, *args, **kwargs)
