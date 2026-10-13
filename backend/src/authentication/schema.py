from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema


class MCPLoginTokenScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.mcp_auth.LoginTokenAuthentication'
    )
    name = 'mcpLoginToken'
    priority = 1

    def get_security_definition(self, auto_schema: AutoSchema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'description': (
                'Existing authenticated Pneumatic user login token.'
            ),
        }


class MCPDelegationScheme(OpenApiAuthenticationExtension):
    target_class = (
        'src.authentication.services.mcp_auth.DelegationAuthentication'
    )
    name = 'mcpDelegation'

    def get_security_definition(self, auto_schema: AutoSchema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'Opaque MCP delegation',
            'description': 'Short-lived credential issued to the MCP service.',
        }
