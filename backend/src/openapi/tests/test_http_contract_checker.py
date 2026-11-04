"""Regressions proving the shared checker detects contract drift."""

import json
from pathlib import Path
import subprocess
import sys
from textwrap import dedent
from types import SimpleNamespace
from typing import Iterator

from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory
from django.test.client import BOUNDARY, encode_multipart
from jsonschema.exceptions import ValidationError
from openapi_schema_validator import OAS30ReadValidator, OAS30WriteValidator
import pytest

from src.openapi.tests.http_contracts import HttpContract


@pytest.fixture
def contract() -> HttpContract:
    value = {'type': 'object', 'required': ['name'], 'properties': {
        'name': {'type': 'string'},
        'count': {'type': 'integer', 'nullable': True},
    }}
    media = {'application/json': {'schema': value}}
    return HttpContract({
        'paths': {
            '/items/{id}': {
                'parameters': [
                    {'name': 'id', 'in': 'path', 'required': True,
                     'schema': {'type': 'integer'}},
                    {'name': 'limit', 'in': 'query',
                     'schema': {'type': 'integer', 'minimum': 1}},
                ],
                'post': {
                    'requestBody': {'required': True, 'content': media},
                    'responses': {
                        '200': {'content': media},
                        '400': {'content': media},
                        '204': {},
                    },
                },
            },
        },
    })


def exchange(
    status: int = 200, path: str = '/items/1',
    value: object = None, content_type: str = 'application/json',
) -> HttpResponse:
    response = HttpResponse(
        json.dumps({'name': 'Item'} if value is None else value),
        status=status, content_type=content_type,
    )
    response.wsgi_request = RequestFactory().post(
        path, data='{"name":"Item"}', content_type='application/json',
    )
    return response


@pytest.mark.parametrize('response,body,error', [
    (exchange(status=202), b'{"name":"Item"}', AssertionError),
    (exchange(content_type='text/plain'), b'{"name":"Item"}',
     AssertionError),
    (exchange(value={'name': 1}), b'{"name":"Item"}', ValidationError),
    (exchange(status=204), b'{"name":"Item"}', AssertionError),
    (exchange(), b'', AssertionError),
    (exchange(), b'{"name":1}', ValidationError),
    (exchange(path='/items/wrong'), b'{"name":"Item"}', ValidationError),
    (exchange(path='/items/1?limit=0'), b'{"name":"Item"}', ValidationError),
])
def test_checker__contract_violation__fails(
    contract, response, body, error,
) -> None:
    with pytest.raises(error):
        contract.exchange(response, body)


def test_checker__nullable_response__passes(contract) -> None:
    response = exchange(value={'name': 'Item', 'count': None})
    contract.exchange(response, b'{"name":"Item"}')


def test_checker__unadvertised_method_405__does_not_cover_operation(
    contract,
) -> None:
    response = exchange(status=405)
    response.wsgi_request = RequestFactory().delete('/items/1')

    contract.exchange(response)

    assert contract.observations == []


def test_checker__documented_method_405__is_contract_violation(
    contract,
) -> None:
    with pytest.raises(AssertionError, match='undocumented status'):
        contract.exchange(exchange(status=405))


def test_checker__negative_request__still_checks_response(contract) -> None:
    contract.exchange(exchange(status=400), b'{"name":1}')
    with pytest.raises(ValidationError):
        contract.exchange(exchange(status=400, value={'name': 1}), b'')


def test_checker__local_ref__resolves_in_document(contract) -> None:
    schema = contract.document['paths']['/items/{id}']['post']['responses'][
        '200'
    ]['content']['application/json']['schema']
    contract.document['components'] = {'schemas': {'Item': schema}}
    contract.validate({'$ref': '#/components/schemas/Item'},
                      {'name': 'Item'}, response=True)
    with pytest.raises(ValidationError):
        contract.validate({'$ref': '#/components/schemas/Item'},
                          {'name': 1}, response=True)


def test_checker__stream__does_not_consume_body(contract) -> None:
    consumed = []

    def stream() -> Iterator[bytes]:
        consumed.append(True)
        yield b'content'

    response = StreamingHttpResponse(stream(), content_type='image/png')
    definition = {'content': {'*/*': {
        'schema': {'type': 'string', 'format': 'binary'},
    }}}
    contract.response_body(response, definition, 'GET /files/id')
    assert not consumed


@pytest.mark.parametrize('content_type,body', [
    ('application/json', b'{"name":"Item"}'),
    ('application/x-www-form-urlencoded', b'name=Item&count=1'),
])
def test_checker__json_and_form_request__validate(
    contract, content_type, body,
) -> None:
    operation = {'requestBody': {'required': True, 'content': {
        content_type: {'schema': {
            'type': 'object', 'required': ['name'], 'properties': {
                'name': {'type': 'string'}, 'count': {'type': 'integer'},
            },
        }},
    }}}
    request = SimpleNamespace(content_type=content_type)
    contract.request_body(operation, request, body)


def test_checker__multipart_request__validates_array_items(contract) -> None:
    # arrange
    mime = f'multipart/form-data; boundary={BOUNDARY}'
    body = encode_multipart(BOUNDARY, {'name': 'Item', 'ids': [1, 2]})
    request = RequestFactory().post('/items/1', body, content_type=mime)
    operation = {'requestBody': {'required': True, 'content': {
        'multipart/form-data': {'schema': {
            'type': 'object', 'properties': {
                'name': {'type': 'string'},
                'ids': {'type': 'array', 'items': {'type': 'integer'}},
            },
        }},
    }}}

    # act / assert
    contract.request_body(operation, request, body)
    bad_body = encode_multipart(BOUNDARY, {'ids': ['wrong']})
    bad_request = RequestFactory().post(
        '/items/1', bad_body, content_type=mime,
    )
    with pytest.raises(ValidationError):
        contract.request_body(operation, bad_request, bad_body)


def test_checker__response_header__validates_presence_and_type(
    contract,
) -> None:
    definition = contract.document['paths']['/items/{id}']['post'][
        'responses'
    ]['200']
    definition['headers'] = {'Retry-After': {
        'required': True, 'schema': {'type': 'integer'},
    }}
    response = exchange()
    with pytest.raises(AssertionError, match='missing Retry-After'):
        contract.exchange(response, b'{"name":"Item"}')
    response['Retry-After'] = 'wrong'
    with pytest.raises(ValidationError):
        contract.exchange(response, b'{"name":"Item"}')
    response['Retry-After'] = '3'
    contract.exchange(response, b'{"name":"Item"}')


@pytest.mark.parametrize('response', [False, True])
@pytest.mark.parametrize('value', [
    'checkout.stripe.com', 'not-a-url', '', '/relative/path',
    '//example.test/path', 'https//example.test/',
    '1https://example.test/', 'ht*tp://example.test/',
    'https://example.test/a b',
    'https://example.test/\n',
    'https://example.test/\t', 'https://example.test/\x00',
    'https://example.test/caf\u00e9', 'https://\u00e9xample.test/',
    'https://example.test/%ZZ', 'https://example.test/%2',
    'https://[2001:db8::zz]/', 'https://[::1/path', 'https://::1/',
    'https://[v1.]/', 'https://first@second@example.test/',
    'https://example.test:abc/', 'https://example.test/a[b]',
    'https://example.test/?value=[x]', 'https://example.test/a\\b',
])
def test_checker__invalid_uri__fails(contract, response, value) -> None:
    with pytest.raises(ValidationError):
        contract.validate(
            {'type': 'string', 'format': 'uri'}, value, response=response,
        )


@pytest.mark.parametrize('response', [False, True])
@pytest.mark.parametrize('value', [
    'https://checkout.stripe.com/session',
    'http://localhost:8000/path?key=value#fragment',
    'https://example.test/a%20b',
    'urn:uuid:12345678-1234-5678-1234-567812345679',
    'mailto:owner@example.test',
    'file:///tmp/avatar.png', 'data:text/plain;charset=utf-8,Hello%20world',
    'https://192.0.2.1/', 'https://[2001:db8::1]/',
    'https://[::ffff:192.0.2.1]/', 'https://[VF.Address:Part]/',
    'HtTpS://EXAMPLE.test:65536/', 'example+v1.0-scheme:', 'file:///?#',
    'https://user:p%40ss@example.test:/',
    "https://user:pass@example.test/a;:@!$&'()*+,=?a/b?c#d/e?f",
    'https://%65xample.test/%e2%82%ac',
])
def test_checker__absolute_uri__passes(contract, response, value) -> None:
    contract.validate(
        {'type': 'string', 'format': 'uri'}, value, response=response,
    )


@pytest.mark.parametrize('response', [False, True])
def test_checker__nullable_uri__accepts_null(contract, response) -> None:
    contract.validate(
        {'type': 'string', 'format': 'uri', 'nullable': True},
        None, response=response,
    )


@pytest.mark.parametrize('response', [False, True])
def test_checker__uri__does_not_depend_on_optional_format_registration(
    contract, monkeypatch, response,
) -> None:
    validator = OAS30ReadValidator if response else OAS30WriteValidator
    checkers = dict(validator.FORMAT_CHECKER.checkers)
    checkers.pop('uri', None)
    monkeypatch.setattr(validator.FORMAT_CHECKER, 'checkers', checkers)

    with pytest.raises(ValidationError):
        contract.validate(
            {'type': 'string', 'format': 'uri'}, 'not-a-url',
            response=response,
        )


@pytest.mark.parametrize('location', ['request', 'response', 'header'])
def test_checker__invalid_uri_exchange__does_not_cover_operation(
    contract, location,
) -> None:
    operation = contract.document['paths']['/items/{id}']['post']
    schema = operation['responses']['200']['content']['application/json'][
        'schema'
    ]
    schema['properties']['name']['format'] = 'uri'
    body = b'{"name":"https://example.test/item"}'
    response = exchange(value={'name': 'https://example.test/item'})
    if location == 'request':
        body = b'{"name":"checkout.stripe.com"}'
    elif location == 'response':
        response = exchange(value={'name': 'checkout.stripe.com'})
    else:
        operation['responses']['200']['headers'] = {'Location': {
            'required': True, 'schema': {'type': 'string', 'format': 'uri'},
        }}
        response['Location'] = 'checkout.stripe.com'

    with pytest.raises(ValidationError):
        contract.exchange(response, body)

    assert contract.observations == []


def test_checker__uri__works_without_optional_format_plugins() -> None:
    script = dedent("""
        import importlib.abc
        import sys

        blocked = {'rfc3986_validator', 'rfc3987', 'rfc3987_syntax'}

        class BlockOptionalURI(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in blocked:
                    raise ModuleNotFoundError(fullname)

        sys.meta_path.insert(0, BlockOptionalURI())
        sys.path.insert(0, sys.argv[1])
        from jsonschema.exceptions import ValidationError
        from src.openapi.tests.http_contracts import HttpContract

        contract = HttpContract({'paths': {}})
        schema = {'type': 'string', 'format': 'uri'}
        for response in (False, True):
            for value in ('not-a-url', 'https://example.test/\\n'):
                try:
                    contract.validate(schema, value, response=response)
                except ValidationError:
                    pass
                else:
                    raise AssertionError(repr(value))
            for value in ('https://example.test/', 'urn:example:contract'):
                contract.validate(schema, value, response=response)
        assert not any(name.split('.')[0] in blocked for name in sys.modules)
    """)
    result = subprocess.run(
        [sys.executable, '-I', '-c', script,
         str(Path(__file__).resolve().parents[3])],
        capture_output=True, text=True, timeout=30, check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
