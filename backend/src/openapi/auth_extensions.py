"""OpenApiAuthenticationExtension for project auth classes."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object
from rest_framework_simplejwt.settings import api_settings


class PneumaticJWTScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.jwt_auth.'
        'PneumaticJWTAuthentication'
    )
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name=getattr(
                api_settings,
                'AUTH_HEADER_NAME',
                'HTTP_AUTHORIZATION',
            ),
            token_prefix=api_settings.AUTH_HEADER_TYPES[0],
            bearer_format='JWT',
        )


class GuestJWTScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.guest_auth.'
        'GuestJWTAuthService'
    )
    name = 'guestJwtAuth'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='HTTP_AUTHORIZATION',
            token_prefix='Bearer',
            bearer_format='JWT',
        )


class PublicAuthScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.public_auth.'
        'PublicAuthService'
    )
    name = 'publicTemplateAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Public-Authorization',
            'description': (
                'Public or embedded template token '
                '(format: Token <jwt>).'
            ),
        }
