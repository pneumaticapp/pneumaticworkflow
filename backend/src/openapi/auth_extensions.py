"""OpenApiAuthenticationExtension for project auth classes."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from django.conf import settings

from src.openapi.reference import HEADER_SECURITY_SCHEMES


def _permission_names(auto_schema) -> set:
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

    def get_security_requirement(self, auto_schema):
        if 'PublicTemplatePermission' in _permission_names(auto_schema):
            return None
        return super().get_security_requirement(auto_schema)

    def get_security_definition(self, auto_schema):
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

    def get_security_requirement(self, auto_schema):
        if (
            settings.PRIVATE_API_CHECK_IP
            and 'PrivateApiPermission' in _permission_names(auto_schema)
        ):
            return None
        return super().get_security_requirement(auto_schema)

    def get_security_definition(self, auto_schema):
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

    def get_security_definition(self, auto_schema):
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

    def get_security_requirement(self, auto_schema):
        names = _permission_names(auto_schema)
        if names & {
            'PublicTemplatePermission',
            'IsAuthenticatedOrPublicTemplate',
        }:
            return {self.name: []}
        return None

    def get_security_definition(self, auto_schema):
        return HEADER_SECURITY_SCHEMES[self.name].copy()


class GuestJWTScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.guest_auth.GuestJWTAuthService'
    )
    name = 'guestAuth'

    def get_security_requirement(self, auto_schema):
        names = _permission_names(auto_schema)
        if names & {
            'UserIsAuthenticated', 'AccountOwnerPermission',
            'UserIsAdminOrAccountOwner', 'StaffPermission',
            'IsSuperuserPermission', 'PublicTemplatePermission',
            'AllowAny',
        }:
            return None
        return {self.name: []}

    def get_security_definition(self, auto_schema):
        return HEADER_SECURITY_SCHEMES[self.name].copy()
