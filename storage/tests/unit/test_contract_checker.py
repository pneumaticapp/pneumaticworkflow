"""Prove that the Files contract checker rejects HTTP contract regressions."""

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import httpx
import pytest
from jsonschema import ValidationError

from tests.contracts import FilesContract

FILE_ID = '12345678-1234-5678-1234-567812345679'
ERROR_REFERENCE = '#/components/schemas/Error'


@pytest.mark.parametrize(
    'value',
    [
        'checkout.stripe.com',
        'not-a-url',
        '',
        '/relative/path',
        '//example.test/path',
        'https//example.test/',
        '1https://example.test/',
        'ht*tp://example.test/',
        'https://example.test/a b',
        'https://example.test/\n',
        'https://example.test/\t',
        'https://example.test/\x00',
        'https://example.test/caf\u00e9',
        'https://\u00e9xample.test/',
        'https://example.test/%ZZ',
        'https://example.test/%2',
        'https://[2001:db8::zz]/',
        'https://[::1/path',
        'https://::1/',
        'https://[v1.]/',
        'https://first@second@example.test/',
        'https://example.test:abc/',
        'https://example.test/a[b]',
        'https://example.test/?value=[x]',
        'https://example.test/a\\b',
    ],
)
def test_checker__invalid_uri__fails(value: str) -> None:
    contract = FilesContract({'paths': {}})

    with pytest.raises(ValidationError):
        contract.validate({'type': 'string', 'format': 'uri'}, value)


@pytest.mark.parametrize(
    'value',
    [
        'https://checkout.stripe.com/session',
        'http://localhost:8000/path?key=value#fragment',
        'https://example.test/a%20b',
        'urn:uuid:12345678-1234-5678-1234-567812345679',
        'mailto:owner@example.test',
        'file:///tmp/avatar.png',
        'data:text/plain;charset=utf-8,Hello%20world',
        'https://192.0.2.1/',
        'https://[2001:db8::1]/',
        'https://[::ffff:192.0.2.1]/',
        'https://[VF.Address:Part]/',
        'HtTpS://EXAMPLE.test:65536/',
        'example+v1.0-scheme:',
        'file:///?#',
        'https://user:p%40ss@example.test:/',
        "https://user:pass@example.test/a;:@!$&'()*+,=?a/b?c#d/e?f",
        'https://%65xample.test/%e2%82%ac',
    ],
)
def test_checker__absolute_uri__passes(value: str) -> None:
    contract = FilesContract({'paths': {}})

    contract.validate({'type': 'string', 'format': 'uri'}, value)


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
        from tests.contracts import FilesContract

        contract = FilesContract({'paths': {}})
        schema = {'type': 'string', 'format': 'uri'}
        for value in ('not-a-url', 'https://example.test/\\n'):
            try:
                contract.validate(schema, value)
            except ValidationError:
                pass
            else:
                raise AssertionError(repr(value))
        for value in ('https://example.test/', 'urn:example:contract'):
            contract.validate(schema, value)
        assert not any(name.split('.')[0] in blocked for name in sys.modules)
    """)
    result = subprocess.run(
        [
            sys.executable,
            '-I',
            '-c',
            script,
            str(Path(__file__).resolve().parents[2]),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('location', ['request', 'response', 'header'])
def test_checker__invalid_uri_exchange__does_not_cover_operation(
    location: str,
) -> None:
    uri = {'type': 'string', 'format': 'uri'}
    media = {
        'application/json': {
            'schema': {
                'type': 'object',
                'required': ['link'],
                'properties': {'link': uri},
            }
        }
    }
    contract = FilesContract(
        {
            'paths': {
                '/files/probe': {
                    'post': {
                        'requestBody': {'required': True, 'content': media},
                        'responses': {
                            '200': {
                                'content': media,
                                'headers': {'Location': {'schema': uri}},
                            }
                        },
                    }
                }
            }
        }
    )
    valid = 'https://example.test/file'
    invalid = 'checkout.stripe.com'
    actual = httpx.Response(
        200,
        json={'link': invalid if location == 'response' else valid},
        headers={'Location': invalid if location == 'header' else valid},
        request=httpx.Request(
            'POST',
            'http://testserver/probe',
            json={'link': invalid if location == 'request' else valid},
        ),
    )

    with pytest.raises(ValidationError):
        contract.exchange(actual)

    assert not contract.observed


@pytest.fixture
def contract() -> FilesContract:
    """A small independent document for validator unit tests only."""
    return FilesContract(
        {
            'openapi': '3.1.0',
            'paths': {
                '/files/upload': {
                    'post': {
                        'requestBody': {
                            'required': True,
                            'content': {
                                'multipart/form-data': {
                                    'schema': {
                                        'type': 'object',
                                        'required': ['file'],
                                        'properties': {
                                            'file': {
                                                'type': 'string',
                                                'format': 'binary',
                                            },
                                        },
                                    },
                                },
                            },
                        },
                        'responses': {'200': {}},
                    },
                },
                '/files/{file_id}': {
                    'get': {
                        'parameters': [
                            {
                                'in': 'path',
                                'name': 'file_id',
                                'required': True,
                                'schema': {'type': 'string', 'format': 'uuid'},
                            },
                        ],
                        'responses': {
                            '200': {
                                'content': {
                                    '*/*': {
                                        'schema': {
                                            'type': 'string',
                                            'format': 'binary',
                                        },
                                    },
                                },
                                'headers': {
                                    'Content-Length': {
                                        'schema': {
                                            'type': 'integer',
                                            'minimum': 0,
                                        },
                                    },
                                    'Accept-Ranges': {
                                        'schema': {
                                            'type': 'string',
                                            'enum': ['bytes'],
                                        },
                                    },
                                },
                            },
                            '401': {
                                'content': {
                                    'application/json': {
                                        'schema': {
                                            '$ref': ERROR_REFERENCE,
                                        },
                                    },
                                },
                            },
                            '416': {},
                        },
                    },
                },
            },
            'components': {
                'schemas': {
                    'Error': {
                        'type': 'object',
                        'required': ['code'],
                        'properties': {
                            'code': {'type': 'string'},
                            'details': {
                                'anyOf': [
                                    {'type': 'null'},
                                    {
                                        'type': 'object',
                                        'required': ['reason'],
                                        'properties': {
                                            'reason': {'type': 'string'},
                                        },
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        },
    )


def response(
    *,
    status: int = 200,
    headers: dict[str, str] | None = None,
    content: bytes = b'abcd',
    file_id: str = FILE_ID,
) -> httpx.Response:
    return httpx.Response(
        status,
        headers=(
            {
                'Content-Type': 'text/plain; charset=utf-8',
                'Content-Length': '4',
                'Accept-Ranges': 'bytes',
            }
            if headers is None
            else headers
        ),
        content=content,
        request=httpx.Request('GET', f'http://testserver/{file_id}'),
    )


@pytest.mark.parametrize('details', [None, {'reason': 'Missing token'}])
def test_checker__component_refs_and_nullable__accepted(
    contract: FilesContract,
    details: dict[str, str] | None,
) -> None:
    actual = httpx.Response(
        401,
        json={'code': 'AUTH_001', 'details': details},
        request=httpx.Request('GET', f'http://testserver/{FILE_ID}'),
    )
    contract.exchange(actual)
    assert contract.observed == {('/files/{file_id}', 'get', 401)}


@pytest.mark.parametrize(
    ('headers', 'content'),
    [
        ({'Content-Type': 'text/html'}, b'{"code":"AUTH_001"}'),
        ({'Content-Type': 'application/json'}, b'{}'),
        ({'Content-Type': 'application/json'}, b'{"code":1}'),
        (
            {'Content-Type': 'application/json'},
            b'{"code":"AUTH_001","details":{"reason":1}}',
        ),
    ],
)
def test_checker__invalid_json_response__rejected(
    contract: FilesContract,
    headers: dict[str, str],
    content: bytes,
) -> None:
    with pytest.raises((AssertionError, ValidationError)):
        contract.exchange(
            response(status=401, headers=headers, content=content)
        )
    assert not contract.observed


@pytest.mark.parametrize(
    'mime', ['image/png', 'application/pdf', 'text/plain']
)
def test_checker__binary_media_range__accepted(
    contract: FilesContract,
    mime: str,
) -> None:
    actual = response()
    actual.headers['Content-Type'] = mime
    contract.exchange(actual)
    assert contract.observed == {('/files/{file_id}', 'get', 200)}


@pytest.mark.parametrize(
    ('name', 'value'),
    [
        ('Content-Length', None),
        ('Content-Length', 'x'),
        ('Content-Length', '5'),
        ('Accept-Ranges', 'none'),
        ('Content-Type', None),
    ],
)
def test_checker__invalid_binary_header__rejected(
    contract: FilesContract,
    name: str,
    value: str | None,
) -> None:
    actual = response()
    if value is None:
        del actual.headers[name]
    else:
        actual.headers[name] = value
    with pytest.raises((AssertionError, ValidationError)):
        contract.exchange(actual)
    assert not contract.observed


@pytest.mark.parametrize(
    ('status', 'content', 'file_id'),
    [
        (410, b'', FILE_ID),
        (416, b'Unexpected', FILE_ID),
        (200, b'abcd', 'bad'),
    ],
)
def test_checker__status_body_or_path_drift__rejected(
    contract: FilesContract,
    status: int,
    content: bytes,
    file_id: str,
) -> None:
    with pytest.raises((AssertionError, ValidationError)):
        contract.exchange(
            response(status=status, content=content, file_id=file_id)
        )
    assert not contract.observed


@pytest.mark.parametrize('name', ['file', 'wrong_field'])
def test_checker__multipart_file_required__enforced(
    contract: FilesContract,
    name: str,
) -> None:
    request = httpx.Request(
        'POST',
        'http://testserver/upload',
        files={
            name: ('contract.bin', b'\x00\xff\x80', 'application/octet-stream')
        },
    )
    request.read()
    actual = httpx.Response(200, request=request)
    if name == 'file':
        contract.exchange(actual)
        assert contract.observed == {('/files/upload', 'post', 200)}
    else:
        with pytest.raises(ValidationError, match='file'):
            contract.exchange(actual)
        assert not contract.observed


def test_checker__successful_request_without_required_body__rejected(
    contract: FilesContract,
) -> None:
    actual = httpx.Response(
        200,
        request=httpx.Request('POST', 'http://testserver/upload'),
    )
    with pytest.raises(AssertionError):
        contract.exchange(actual)
    assert not contract.observed


def test_checker__present_empty_filename__accepted(
    contract: FilesContract,
) -> None:
    body = (
        b'--contract\r\n'
        b'Content-Disposition: form-data; name="file"; filename=""\r\n'
        b'Content-Type: text/plain\r\n\r\ndata\r\n--contract--\r\n'
    )
    request = httpx.Request(
        'POST',
        'http://testserver/upload',
        headers={'Content-Type': 'multipart/form-data; boundary=contract'},
        content=body,
    )
    contract.exchange(httpx.Response(200, request=request))
    assert contract.observed == {('/files/upload', 'post', 200)}


@pytest.mark.parametrize(
    'disposition',
    [b'form-data; name="file"', b'form-data; filename="contract.txt"'],
    ids=['text-instead-of-file', 'missing-part-name'],
)
def test_checker__multipart_without_name_or_file__rejected(
    contract: FilesContract,
    disposition: bytes,
) -> None:
    body = (
        b'--contract\r\nContent-Disposition: '
        + disposition
        + b'\r\nContent-Type: text/plain\r\n\r\ndata\r\n--contract--\r\n'
    )
    request = httpx.Request(
        'POST',
        'http://testserver/upload',
        headers={'Content-Type': 'multipart/form-data; boundary=contract'},
        content=body,
    )
    with pytest.raises((AssertionError, ValidationError)):
        contract.exchange(httpx.Response(200, request=request))
    assert not contract.observed


def test_checker__file_and_regular_form_field__accepted(
    contract: FilesContract,
) -> None:
    request = httpx.Request(
        'POST',
        'http://testserver/upload',
        data={'description': 'A regular form field'},
        files={'file': ('contract.txt', b'data', 'text/plain')},
    )
    request.read()
    contract.exchange(httpx.Response(200, request=request))
    assert contract.observed == {('/files/upload', 'post', 200)}


def test_checker__content_type_name_without_filename__rejected(
    contract: FilesContract,
) -> None:
    body = (
        b'--contract\r\n'
        b'Content-Disposition: form-data; name="file"\r\n'
        b'Content-Type: application/octet-stream; name="not-a-file.bin"'
        b'\r\n\r\ndata\r\n--contract--\r\n'
    )
    request = httpx.Request(
        'POST',
        'http://testserver/upload',
        headers={'Content-Type': 'multipart/form-data; boundary=contract'},
        content=body,
    )
    with pytest.raises(AssertionError, match='must include a filename'):
        contract.exchange(httpx.Response(200, request=request))
    assert not contract.observed


def test_checker__operation_not_in_schema__rejected(
    contract: FilesContract,
) -> None:
    actual = httpx.Response(
        200,
        request=httpx.Request('DELETE', f'http://testserver/{FILE_ID}'),
    )
    with pytest.raises(AssertionError, match='Undocumented operation: DELETE'):
        contract.exchange(actual)
    assert not contract.observed


def test_checker__static_path_with_another_method__matches_parameter_route(
    contract: FilesContract,
) -> None:
    parameter = contract.document['paths']['/files/{file_id}']['get'][
        'parameters'
    ][0]
    parameter['schema'] = {'type': 'string'}
    contract.exchange(response(file_id='upload'))
    assert contract.observed == {('/files/{file_id}', 'get', 200)}


@pytest.mark.parametrize('addition', ['existing', 'status', 'method', 'path'])
def test_coverage_gate__new_outcome_without_http_exchange__fails(
    contract: FilesContract,
    addition: str,
) -> None:
    contract.observed = {
        ('/files/upload', 'post', 200),
        ('/files/{file_id}', 'get', 200),
        ('/files/{file_id}', 'get', 401),
        ('/files/{file_id}', 'get', 416),
    }
    contract.assert_complete()
    paths = contract.document['paths']
    if addition == 'status':
        paths['/files/{file_id}']['get']['responses']['503'] = {}
    elif addition == 'method':
        paths['/files/{file_id}']['head'] = {'responses': {'200': {}}}
    elif addition == 'path':
        paths['/files/new'] = {'post': {'responses': {'201': {}}}}
    else:
        contract.observed.remove(('/files/{file_id}', 'get', 416))
    with pytest.raises(AssertionError, match='lack HTTP coverage'):
        contract.assert_complete()


def test_coverage_gate__pagination_not_applicable__explicit(
    contract: FilesContract,
) -> None:
    contract.observed = {
        ('/files/upload', 'post', 200),
        ('/files/{file_id}', 'get', 200),
        ('/files/{file_id}', 'get', 401),
        ('/files/{file_id}', 'get', 416),
    }
    contract.document['paths']['/files/{file_id}']['get']['parameters'].append(
        {'in': 'query', 'name': 'limit', 'schema': {'type': 'integer'}},
    )
    with pytest.raises(AssertionError, match='no pagination'):
        contract.assert_complete()
