"""Blank URL fields retain their actual serializer semantics in OpenAPI."""

from jsonschema.exceptions import ValidationError
from openapi_schema_validator import OAS30ReadValidator, OAS30WriteValidator
import pytest
from rest_framework.exceptions import ValidationError as LiveValidationError

from src.ai.serializers import AIAgentSerializer
from src.openapi.tests.http_contracts import HttpContract


@pytest.mark.parametrize('component,response', [
    ('Group', True), ('GroupRequest', False),
])
@pytest.mark.parametrize('value', [
    '', None, 'https://example.test/group-photo.png',
])
def test_group_photo__blank_nullable_uri__matches_live_field(
    http_contract: HttpContract, component: str, response: bool, value: object,
) -> None:
    schema = http_contract.document['components']['schemas'][component][
        'properties'
    ]['photo']

    http_contract.validate(schema, value, response=response)

    with pytest.raises(ValidationError):
        http_contract.validate(schema, 'not-a-url', response=response)


@pytest.mark.parametrize('component,response', [
    ('AIAgent', True), ('AIAgentRequest', False),
    ('PatchedAIAgentRequest', False),
])
@pytest.mark.parametrize('value', [
    '', None, 'https://example.test/agent-photo.png',
])
def test_ai_agent_photo__blank_nullable_uri__matches_live_field(
    http_contract: HttpContract, component: str, response: bool, value: object,
) -> None:
    field = AIAgentSerializer().fields['photo']
    schema = http_contract.document['components']['schemas'][component][
        'properties'
    ]['photo']

    assert field.run_validation(value) == value
    http_contract.validate(schema, value, response=response)

    with pytest.raises(ValidationError):
        http_contract.validate(schema, 'not-a-url', response=response)


@pytest.mark.parametrize('component,response', [
    ('AIAgent', True), ('AIAgentRequest', False),
    ('PatchedAIAgentRequest', False),
])
@pytest.mark.parametrize('length', [1024, 1025])
def test_ai_agent_photo__uri_length_boundary__matches_live_field(
    http_contract: HttpContract, component: str, response: bool, length: int,
) -> None:
    field = AIAgentSerializer().fields['photo']
    schema = http_contract.document['components']['schemas'][component][
        'properties'
    ]['photo']
    prefix = 'https://example.test/'
    value = prefix + 'a' * (length - len(prefix))
    assert field.max_length == 1024

    if length == 1024:
        assert field.run_validation(value) == value
        http_contract.validate(schema, value, response=response)
    else:
        with pytest.raises(LiveValidationError, match='1024'):
            field.run_validation(value)
        with pytest.raises(ValidationError):
            http_contract.validate(schema, value, response=response)


@pytest.mark.parametrize('component,response', [
    ('AIAgent', True), ('AIAgentRequest', False),
    ('PatchedAIAgentRequest', False),
])
def test_ai_agent_photo__blank_alternative__independent_of_format_checks(
    http_contract: HttpContract, component: str, response: bool,
) -> None:
    schema = http_contract.document['components']['schemas'][component][
        'properties'
    ]['photo']
    validator = OAS30ReadValidator if response else OAS30WriteValidator

    # Tools may treat format as an annotation; blank remains unambiguous.
    validator(schema).validate('')
