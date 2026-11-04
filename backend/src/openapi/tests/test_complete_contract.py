"""Regression checks for machine-readable contracts used by integrations."""

import ast
import inspect
import textwrap
from datetime import datetime, timezone

import pytest
from drf_spectacular.generators import EndpointEnumerator, SchemaGenerator
from jsonschema import Draft4Validator, validators
from rest_framework.exceptions import ValidationError

from src.generics.fields import TimeStampField
from src.generics.mixins.views import BaseResponseMixin
from src.processes.enums import (
    TaskOrdering,
    WorkflowApiStatus,
    WorkflowOrdering,
)
from src.processes.serializers.workflows.workflow import (
    WorkflowUpdateSerializer,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope='module')
def contract_schema() -> dict:
    return SchemaGenerator().get_schema(request=None, public=True)


def _response_schema(schema: dict, path: str, method: str = 'get') -> dict:
    return schema['paths'][path][method]['responses']['200']['content'][
        'application/json'
    ]['schema']


def _resolve(schema: dict, value: dict) -> dict:
    while '$ref' in value:
        value = schema['components']['schemas'][value['$ref'].split('/')[-1]]
    if len(value.get('allOf', [])) == 1:
        return {
            **_resolve(schema, value['allOf'][0]),
            **{key: item for key, item in value.items() if key != 'allOf'},
        }
    return value


def _validate_nullable_type(validator, types, instance, schema):
    """OpenAPI 3.0 nullable applies to the schema declaring the type."""
    if instance is None and schema.get('nullable', False):
        return
    yield from Draft4Validator.VALIDATORS['type'](
        validator, types, instance, schema,
    )


NullableDraft4Validator = validators.extend(
    Draft4Validator, {'type': _validate_nullable_type},
)


def test_security_requirements__all_resolve__ok(contract_schema):
    # arrange
    schemes = contract_schema['components']['securitySchemes']
    methods = {'get', 'post', 'put', 'patch', 'delete'}

    # act
    missing = [
        (path, method, name)
        for path, item in contract_schema['paths'].items()
        for method, operation in item.items()
        if method in methods
        for requirement in operation.get('security', [])
        for name in requirement
        if name not in schemes
    ]

    # assert
    assert not missing
    assert schemes['publicTemplateAuth']['name'] == 'X-Public-Authorization'
    assert schemes['guestAuth']['name'] == 'X-Guest-Authorization'


def test_security_requirements__public_guest_and_user__correct(
    contract_schema,
):
    # arrange
    paths = contract_schema['paths']

    # act
    public = paths['/templates/public']['get']['security']
    guest = paths['/v2/tasks/{id}/complete']['post']['security']
    user = paths['/workflows']['get']['security']

    # assert
    assert public == [{'publicTemplateAuth': []}]
    assert {'guestAuth': []} in guest
    assert {'guestAuth': []} not in user
    assert {'publicTemplateAuth': []} not in user


def test_timestamp__runtime_and_response_schema__match(contract_schema):
    # arrange
    field = TimeStampField()
    date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    properties = contract_schema['components']['schemas']['WorkflowList'][
        'properties'
    ]

    # act
    value = field.to_representation(date)
    parsed = field.run_validation('1767225600')

    # assert
    assert value == 1767225600.0
    assert isinstance(value, float)
    assert parsed.timestamp() == value
    assert properties['date_created_tsp']['type'] == 'number'
    assert properties['date_created_tsp'].get('format') != 'date-time'
    with pytest.raises(ValidationError):
        field.run_validation('2026-01-01T00:00:00Z')


def test_timestamp__request_components_separate__ok(contract_schema):
    # arrange
    operation = contract_schema['paths']['/v2/tasks/{id}/due-date']['post']
    body = operation['requestBody']['content']['application/json']['schema']

    # act
    request = _resolve(contract_schema, body)
    timestamp = request['properties']['due_date_tsp']

    # assert
    assert {choice['type'] for choice in timestamp['oneOf']} == {
        'number',
        'string',
    }
    assert body['$ref'].endswith('Request')
    validator = Draft4Validator(timestamp)
    assert validator.is_valid(1767225600.0)
    assert validator.is_valid('1767225600')
    assert not validator.is_valid('2026-01-01T00:00:00Z')
    assert not validator.is_valid(None)


@pytest.mark.parametrize('method', ['patch', 'put'])
@pytest.mark.parametrize('value,valid', [
    (None, True),
    (1767225600.0, True),
    ('1767225600', True),
    ('2026-01-01T00:00:00Z', False),
    ('', False),
])
def test_timestamp__nullable_workflow_request__matches_field(
    contract_schema, method, value, valid,
):
    # arrange
    operation = contract_schema['paths']['/workflows/{id}'][method]
    body = operation['requestBody']['content']['application/json']['schema']
    request = _resolve(contract_schema, body)
    timestamp = request['properties']['due_date_tsp']
    field = WorkflowUpdateSerializer().fields['due_date_tsp']

    # act
    accepted = NullableDraft4Validator(timestamp).is_valid(value)

    # assert
    assert accepted is valid
    if valid:
        parsed = field.run_validation(value)
        if value is None:
            assert parsed is None
        else:
            assert parsed.timestamp() == float(value)
    else:
        with pytest.raises(ValidationError):
            field.run_validation(value)


def test_nested_response_fields__types__correct(contract_schema):
    # arrange
    schemas = contract_schema['components']['schemas']
    workflow = schemas['WorkflowList']['properties']
    task = schemas['Task']['properties']

    # act
    owners = workflow['owners']
    tasks = workflow['tasks']
    fields = workflow['fields']

    # assert
    assert owners['type'] == 'array'
    assert owners['items']['type'] == 'integer'
    assert tasks['type'] == 'array'
    assert fields['type'] == 'array'
    assert _resolve(contract_schema, task['workflow'])['type'] == 'object'
    assert task['sub_workflows']['type'] == 'array'
    assert task['is_completed']['type'] == 'boolean'
    assert task['is_read_only_viewer']['type'] == 'boolean'
    assert (
        schemas['AccountPlan']['properties']['trial_is_active']['type']
        == 'boolean'
    )


@pytest.mark.parametrize(
    'path',
    [
        '/ai/providers/{id}/models',
        '/ai/vendors',
        '/webhooks/events',
        '/reports/dashboard/workflows/breakdown',
        '/reports/dashboard/workflows/by-tasks',
        '/reports/dashboard/tasks/breakdown',
        '/reports/dashboard/tasks/by-steps',
    ],
)
def test_plain_array_responses__no_fake_pagination__ok(
    contract_schema,
    path,
):
    # arrange
    operation = contract_schema['paths'][path]['get']

    # act
    response = _resolve(
        contract_schema,
        _response_schema(
            contract_schema,
            path,
        ),
    )
    query = {
        parameter['name']
        for parameter in operation.get('parameters', [])
        if parameter['in'] == 'query'
    }

    # assert
    assert response['type'] == 'array'
    assert not {'limit', 'offset'} & query


@pytest.mark.parametrize(
    'path',
    [
        '/accounts/users',
        '/accounts/public/users',
    ],
)
def test_optional_pagination__both_shapes__documented(contract_schema, path):
    # arrange
    response = _response_schema(contract_schema, path)

    # act
    variants = [
        _resolve(contract_schema, value) for value in response['oneOf']
    ]

    # assert
    assert {value['type'] for value in variants} == {'array', 'object'}
    envelope = next(value for value in variants if value['type'] == 'object')
    assert {'count', 'next', 'previous', 'results'} <= set(
        envelope['properties'],
    )


def test_action_pagination__default_limit_always_envelope__ok(contract_schema):
    # arrange
    schema = _response_schema(contract_schema, '/workflows')

    # act
    response = _resolve(contract_schema, schema)

    # assert
    assert response['type'] == 'object'
    assert response['properties']['results']['type'] == 'array'
    assert 'oneOf' not in schema


@pytest.mark.parametrize(
    'path,name,choices',
    [
        ('/workflows', 'status', WorkflowApiStatus.CHOICES),
        ('/workflows', 'ordering', WorkflowOrdering.CHOICES),
        ('/v3/tasks', 'ordering', TaskOrdering.CHOICES),
    ],
)
def test_query_enums__match_accepted_values__ok(
    contract_schema,
    path,
    name,
    choices,
):
    # arrange
    parameters = contract_schema['paths'][path]['get']['parameters']

    # act
    parameter = next(value for value in parameters if value['name'] == name)

    # assert
    assert set(parameter['schema']['enum']) == {value for value, _ in choices}


def test_empty_success_status__matches_helper__ok(contract_schema):
    # arrange
    generator = SchemaGenerator()
    endpoints = EndpointEnumerator().get_api_endpoints()
    actual_status = BaseResponseMixin().response_ok().status_code
    mismatches = []

    # act
    for path, _regex, method, callback in endpoints:
        actions = getattr(callback, 'actions', {})
        name = actions.get(method.lower(), method.lower())
        function = getattr(callback.cls, name, None)
        if function is None:
            continue
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        empty_success = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'response_ok'
            and not node.args
            and not node.keywords
            for node in ast.walk(tree)
        )
        if not empty_success:
            continue
        view = generator.create_view(callback, method)
        normalized = generator.coerce_path(path, method, view)
        responses = (
            contract_schema['paths']
            .get(normalized, {})
            .get(
                method.lower(),
                {},
            )
            .get('responses', {})
        )
        if str(actual_status) not in responses:
            mismatches.append((method, normalized))

    # assert
    assert actual_status == 204
    assert not mismatches, mismatches
