"""OpenApiAuthenticationExtension for project auth classes."""

from typing import TYPE_CHECKING, Optional

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from src.openapi.reference import HEADER_SECURITY_SCHEMES

if TYPE_CHECKING:
    from drf_spectacular.openapi import AutoSchema


def _permission_names(auto_schema: 'AutoSchema') -> set[str]:
    return {
        type(permission).__name__
        for permission in auto_schema.view.get_permissions()
    }


class PneumaticTokenScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.user_auth.'
        'PneumaticTokenAuthentication'
    )
    name = 'tokenAuth'

    def get_security_requirement(
        self, auto_schema: 'AutoSchema',
    ) -> Optional[dict[str, list[str]]]:
        if 'PublicTemplatePermission' in _permission_names(auto_schema):
            return None
        return super().get_security_requirement(auto_schema)

    def get_security_definition(self, auto_schema: 'AutoSchema') -> dict:
        return build_bearer_security_scheme_object(
            header_name='HTTP_AUTHORIZATION',
            token_prefix='Bearer',
        )


class APIKeyScheme(PneumaticTokenScheme):
    target_class = (
        'src.authentication.services.api_key_auth.APIKeyAuthentication'
    )
    name = 'apiKeyAuth'
    priority = 1

    def get_security_requirement(
        self, auto_schema: 'AutoSchema',
    ) -> Optional[dict[str, list[str]]]:
        if (
            settings.PRIVATE_API_CHECK_IP
            and 'PrivateApiPermission' in _permission_names(auto_schema)
        ):
            return None
        return super().get_security_requirement(auto_schema)

    def get_security_definition(self, auto_schema: 'AutoSchema') -> dict:
        return {
            **super().get_security_definition(auto_schema),
            'description': (
                'Pneumatic API key, supplied as Authorization: Bearer '
                '<api_key>. API keys have a pn- prefix and may expire '
                'or be revoked. Role, billing and private-IP gates '
                'still apply.'
            ),
        }


class PneumaticJWTScheme(PneumaticTokenScheme):
    target_class = (
        'src.authentication.services.jwt_auth.PneumaticJWTAuthentication'
    )
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema: 'AutoSchema') -> dict:
        return build_bearer_security_scheme_object(
            header_name='HTTP_AUTHORIZATION',
            token_prefix='Bearer',
            bearer_format='JWT',
        )


class PublicTemplateScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.public_auth.PublicAuthService'
    )
    name = 'publicTemplateAuth'

    def get_security_requirement(
        self, auto_schema: 'AutoSchema',
    ) -> Optional[dict[str, list[str]]]:
        names = _permission_names(auto_schema)
        if names & {
            'PublicTemplatePermission',
            'IsAuthenticatedOrPublicTemplate',
        }:
            return {self.name: []}
        return None

    def get_security_definition(self, auto_schema: 'AutoSchema') -> dict:
        return HEADER_SECURITY_SCHEMES[self.name].copy()


class GuestJWTScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.guest_auth.GuestJWTAuthService'
    )
    name = 'guestAuth'

    def get_security_requirement(
        self, auto_schema: 'AutoSchema',
    ) -> Optional[dict[str, list[str]]]:
        names = _permission_names(auto_schema)
        if names & {
            'UserIsAuthenticated', 'AccountOwnerPermission',
            'UserIsAdminOrAccountOwner', 'StaffPermission',
            'IsSuperuserPermission', 'PublicTemplatePermission',
            'AllowAny',
        }:
            return None
        return {self.name: []}

    def get_security_definition(self, auto_schema: 'AutoSchema') -> dict:
        return HEADER_SECURITY_SCHEMES[self.name].copy()
