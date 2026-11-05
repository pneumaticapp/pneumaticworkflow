"""Coverage requires validated success, failure and nonempty list exchanges."""

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

from django.http import HttpResponse
from django.test import RequestFactory
from jsonschema.exceptions import ValidationError
import pytest

from src.openapi.tests.contract_coverage import (
    coverage_errors,
    coverage_report,
)
from src.openapi.tests.http_contracts import HttpContract


@pytest.fixture
def coverage_contract() -> HttpContract:
    item = {
        'type': 'object', 'required': ['id'],
        'properties': {'id': {'type': 'integer'}},
    }
    rows = {'type': 'array', 'items': item}
    envelope = {
        'type': 'object',
        'required': ['count', 'next', 'previous', 'results'],
        'properties': {
            'count': {'type': 'integer'},
            'next': {'type': 'string', 'nullable': True},
            'previous': {'type': 'string', 'nullable': True},
            'results': rows,
        },
    }
    return HttpContract({'paths': {'/items': {'get': {
        'responses': {
            '200': {'content': {'application/json': {
                'schema': {'oneOf': [rows, envelope]},
            }}},
            '400': {'content': {'application/json': {
                'schema': {'type': 'object'},
            }}},
        },
    }}}})


def record(contract, path='/items', value=None, status=200, method='get',
           **kwargs) -> None:
    body = json.dumps([{'id': 1}] if value is None else value)
    response = HttpResponse(
        body, status=status, content_type='application/json',
    )
    response.wsgi_request = getattr(RequestFactory(), method)(path)
    if method == 'head' or status in (204, 304):
        response.content = b''
    contract.exchange(response, case='case', **kwargs)


def test_coverage__success_error_and_two_modes__complete(
    coverage_contract,
) -> None:
    record(coverage_contract)
    record(coverage_contract, '/items?limit=1', {
        'count': 2, 'next': 'https://example.test/items?offset=1',
        'previous': None, 'results': [{'id': 1}],
    })
    record(coverage_contract, value={'detail': 'Invalid limit'}, status=400)

    report = coverage_report(coverage_contract)

    assert report['covered_operations'] == report['operation_count'] == 1
    assert report['paginated_operations'] == 1
    assert report['validated_status_pairs'] == 2
    assert report['gaps'] == []
    assert coverage_errors(report) == []


@pytest.mark.parametrize('status,value', [
    (200, []), (400, {'detail': 'Error'}),
])
def test_coverage__empty_or_negative_list__does_not_cover_pagination(
    coverage_contract, status, value,
) -> None:
    record(coverage_contract, value=value, status=status)
    record(coverage_contract, '/items?limit=1', value=value, status=status)

    gap = coverage_report(coverage_contract)['gaps'][0]

    assert gap['missing_modes'] == ['default', 'limit=1']


def test_coverage__new_operation__requires_its_own_exchanges(
    coverage_contract,
) -> None:
    coverage_contract.document['paths']['/new'] = {
        'get': {'responses': {'204': {}}},
    }

    report = coverage_report(coverage_contract)

    assert report['operation_count'] == 2
    assert not report['gaps'][1]['has_success']
    assert report['gaps'][1]['missing_success'] == [204]
    assert 'GET /new' in coverage_errors(report)[1]


def test_coverage__default_response__still_requires_real_success(
    coverage_contract,
) -> None:
    operation = coverage_contract.document['paths']['/items']['get']
    operation['responses'] = {'default': operation['responses']['400']}
    record(coverage_contract, value={'detail': 'Error'}, status=500)

    report = coverage_report(coverage_contract)

    assert report['covered_operations'] == 0
    assert report['gaps'][0]['has_success'] is False


def test_coverage__head__does_not_cover_get(coverage_contract) -> None:
    record(coverage_contract, method='head')

    assert coverage_contract.observations == []
    assert coverage_report(coverage_contract)['covered_operations'] == 0


def test_coverage__unresolved_url__does_not_cover_operation(
    coverage_contract,
) -> None:
    record(coverage_contract, status=404)

    assert coverage_contract.observations == []


def test_coverage__invalid_response__is_not_recorded(
    coverage_contract,
) -> None:
    with pytest.raises(ValidationError):
        record(coverage_contract, value=[{'id': 'wrong'}])

    assert coverage_contract.observations == []


def test_coverage__all_published_success_statuses__required(
    coverage_contract,
) -> None:
    operation = coverage_contract.document['paths']['/items']['get']
    operation['responses']['204'] = {}
    record(coverage_contract)

    assert coverage_report(coverage_contract)['gaps'][0][
        'missing_success'
    ] == [204]


@pytest.mark.parametrize('status', [403, 429, 500])
def test_coverage__every_published_error_status__required(
    coverage_contract, status: int,
) -> None:
    operation = coverage_contract.document['paths']['/items']['get']
    operation['responses'][str(status)] = operation['responses']['400']
    record(coverage_contract)
    record(coverage_contract, '/items?limit=1', [{'id': 1}])
    record(coverage_contract, value={'detail': 'Invalid input'}, status=400)

    report = coverage_report(coverage_contract)

    assert report['covered_operations'] == 0
    assert report['gaps'][0]['has_error'] is True
    assert report['gaps'][0]['missing_error'] == [status]
    assert f'missing error statuses=[{status}]' in coverage_errors(report)[0]

    record(coverage_contract, value={'detail': 'Error'}, status=status)

    assert coverage_errors(coverage_report(coverage_contract)) == []


def test_coverage__undocumented_error__cannot_cover_declared_error(
    coverage_contract,
) -> None:
    operation = coverage_contract.document['paths']['/items']['get']
    operation['responses']['403'] = operation['responses']['400']
    record(coverage_contract)
    record(coverage_contract, '/items?limit=1', [{'id': 1}])
    record(coverage_contract, value={'detail': 'Invalid input'}, status=400)

    with pytest.raises(AssertionError, match='undocumented status'):
        record(coverage_contract, value={'detail': 'Error'}, status=402)

    report = coverage_report(coverage_contract)

    assert report['gaps'][0]['missing_error'] == [403]
    assert 402 not in report['operations'][0]['validated_statuses']


def test_coverage__semantic_failure__cannot_count_as_success() -> None:
    path = '/accounts/digest/unsubscribe'
    contract = HttpContract({'paths': {path: {'get': {'responses': {
        '200': {'content': {
            'application/json': {'schema': {'type': 'array'}},
        }},
    }}}}})
    record(contract, path, semantic_errors=frozenset({(path, 'get')}))
    gap = coverage_report(contract)['gaps'][0]
    assert gap['has_error'] is True
    assert gap['has_success'] is False

    record(contract, path, semantic_successes=frozenset({(path, 'get')}))

    assert coverage_report(contract)['gaps'] == []


def test_coverage__unclassified_token_result__is_neither_outcome() -> None:
    path = '/accounts/digest/unsubscribe'
    contract = HttpContract({'paths': {path: {'get': {'responses': {
        '200': {'content': {
            'application/json': {'schema': {'type': 'array'}},
        }},
    }}}}})
    record(contract, path)

    gap = coverage_report(contract)['gaps'][0]

    assert gap['has_error'] is False
    assert gap['has_success'] is False


def test_coverage__renamed_selected_case__is_reported() -> None:
    report = {'gaps': [], 'missing_selected_cases': ['old::test_name']}

    assert coverage_errors(report) == [
        'Selected contract case was not collected: old::test_name',
    ]


@pytest.mark.parametrize('method', ['head', 'options', 'trace'])
def test_coverage__explicit_http_method__requires_real_exchange(
    method,
) -> None:
    contract = HttpContract({'paths': {'/extra': {
        method: {'responses': {'204': {}}},
    }}})
    assert coverage_report(contract)['covered_operations'] == 0
    assert coverage_report(contract)['operation_count'] == 1

    record(contract, '/extra', status=204, method=method)

    assert coverage_report(contract)['covered_operations'] == 1


def test_coverage__semantic_error__does_not_validate_invalid_request() -> None:
    path = '/accounts/digest/unsubscribe'
    content = {'application/json': {'schema': {'type': 'array'}}}
    contract = HttpContract({'paths': {path: {'post': {
        'requestBody': {'required': True, 'content': content},
        'responses': {'200': {'content': content}},
    }}}})

    record(contract, path, method='post',
           semantic_errors=frozenset({(path, 'post')}))

    assert contract.observations[0]['outcome'] == 'error'


def test_coverage__empty_schema__reports_failure() -> None:
    report = coverage_report(HttpContract({'paths': {}}))

    assert coverage_errors(report) == [
        'Core schema contains no HTTP operations.',
    ]


def test_coverage__collection_only__does_not_require_exchanges() -> None:
    source = Path(__file__).resolve().parents[3] / 'conftest.py'
    spec = spec_from_file_location('backend_contract_hooks', source)
    hooks = module_from_spec(spec)
    spec.loader.exec_module(hooks)
    session = SimpleNamespace(
        config=SimpleNamespace(getoption=lambda name: name == 'collectonly'),
        exitstatus=0,
    )

    hooks.pytest_sessionfinish(session, 0)

    assert session.exitstatus == 0
