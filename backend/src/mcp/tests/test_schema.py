import pytest
from drf_spectacular.generators import SchemaGenerator
from pytest_django.fixtures import SettingsWrapper


@pytest.mark.django_db
def test_schema__mcp_public_security_and_private_routes__exact(
    mcp_settings: SettingsWrapper,
):
    # arrange
    generator = SchemaGenerator()

    # act
    schema = generator.get_schema(request=None, public=True)

    # assert
    assert schema['paths']['/integrations/mcp/login-code']['post'][
        'security'
    ] == [{'mcpLoginToken': []}]
    assert schema['components']['securitySchemes']['mcpLoginToken'] == {
        'type': 'http',
        'scheme': 'bearer',
        'description': 'Existing authenticated Pneumatic user login token.',
    }
    assert '/internal/mcp/introspect' not in schema['paths']
    assert '/internal/mcp/delegate' not in schema['paths']
    assert '/internal/mcp/validate-files' not in schema['paths']
    assert '/internal/mcp/complete-upload' not in schema['paths']
    assert '/internal/mcp/cleanup-upload' not in schema['paths']
