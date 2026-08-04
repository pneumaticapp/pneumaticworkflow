"""OpenApiAuthenticationExtension for project auth classes."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class PneumaticTokenScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.user_auth.'
        'PneumaticTokenAuthentication'
    )
    name = 'tokenAuth'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='HTTP_AUTHORIZATION',
            token_prefix='Bearer',
        )
