"""HTTP contract assertions used only by pytest, never by application views."""

from fnmatch import fnmatchcase
from ipaddress import AddressValueError, IPv6Address
from io import BytesIO
import json
import re
from typing import Any

from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.http import HttpResponse, QueryDict
from django.http.multipartparser import MultiPartParser
from jsonschema import FormatChecker, RefResolver
from jsonschema.exceptions import best_match
from openapi_schema_validator import OAS30ReadValidator, OAS30WriteValidator

from src.openapi.tests.contract_coverage import SEMANTIC_ERRORS


_URI_CHAR = r"(?:[A-Za-z0-9._~!$&'()*+,;=-]|%[0-9A-Fa-f]{2})"
_PCHAR = rf'(?:{_URI_CHAR}|[:@])'
_URI = re.compile(
    r'[A-Za-z][A-Za-z0-9+.-]*:(?://([^/?#]*))?([^?#]*)'
    r'(?:\?([^#]*))?(?:#(.*))?',
)
_URI_PATH = re.compile(rf'(?:{_PCHAR}|/)*')
_URI_QUERY = re.compile(rf'(?:{_PCHAR}|[/?])*')
_URI_HOST = re.compile(rf'{_URI_CHAR}*')
_URI_USERINFO = re.compile(rf'(?:{_URI_CHAR}|:)*')
_IPV_FUTURE = re.compile(
    r"[vV][0-9A-Fa-f]+\.[A-Za-z0-9._~!$&'()*+,;=:-]+",
)


def _is_uri_ip_literal(value: str) -> bool:
    if '%' in value:
        return False
    if _IPV_FUTURE.fullmatch(value):
        return True
    try:
        IPv6Address(value)
    except AddressValueError:
        return False
    return True


def _is_uri_authority(value: str) -> bool:
    userinfo, separator, host = value.rpartition('@')
    if separator and not _URI_USERINFO.fullmatch(userinfo):
        return False
    if not separator:
        host = value
    if host.startswith('['):
        literal, closing, suffix = host[1:].partition(']')
        if not closing or not _is_uri_ip_literal(literal):
            return False
        return not suffix or (
            suffix.startswith(':')
            and re.fullmatch(r'[0-9]*', suffix[1:]) is not None
        )
    hostname, separator, port = host.rpartition(':')
    if not separator:
        hostname = host
    return _URI_HOST.fullmatch(hostname) is not None and (
        not separator or re.fullmatch(r'[0-9]*', port) is not None
    )


def _is_uri(value: Any) -> bool:
    """Check RFC 3986 URI components without parser normalization."""
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r'[\x21-\x7e]+', value):
        return False
    match = _URI.fullmatch(value)
    if match is None:
        return False
    authority, path, query, fragment = match.groups()
    return (
        (authority is None or _is_uri_authority(authority))
        and _URI_PATH.fullmatch(path) is not None
        and _URI_QUERY.fullmatch(query or '') is not None
        and _URI_QUERY.fullmatch(fragment or '') is not None
    )


class HttpContract:
    def __init__(self, document: dict) -> None:
        self.document = document
        self.observations = []
        self.routes = []
        for path, item in sorted(
            document['paths'].items(), key=lambda pair: pair[0].count('{'),
        ):
            names = re.findall(r'\{([^}]+)\}', path)
            pattern = re.escape(path)
            for name in names:
                pattern = pattern.replace(
                    re.escape('{' + name + '}'), f'(?P<{name}>[^/]+)',
                )
            self.routes.append((path, re.compile(pattern + '$'), item))

    def validate(
        self, schema: dict, value: Any, *, response: bool,
    ) -> None:
        validator = OAS30ReadValidator if response else OAS30WriteValidator
        formats = FormatChecker()
        formats.checkers.update(validator.FORMAT_CHECKER.checkers)
        formats.checks('uri')(_is_uri)
        checker = validator(
            schema,
            resolver=RefResolver.from_schema(self.document),
            format_checker=formats,
        )
        error = best_match(checker.iter_errors(value))
        if error is not None:
            raise error

    def resolve(self, value: dict) -> dict:
        while '$ref' in value:
            reference = value['$ref']
            assert reference.startswith('#/'), 'Only local schema refs allowed'
            value = self.document
            for segment in reference[2:].split('/'):
                value = value[segment.replace('~1', '/').replace('~0', '~')]
        return value

    @staticmethod
    def media(content: dict, content_type: str) -> dict:
        mime = content_type.split(';', 1)[0].lower()
        for pattern, definition in sorted(content.items(), reverse=True):
            if fnmatchcase(mime, pattern):
                return definition
        raise AssertionError(f'Undocumented Content-Type: {mime}')

    def exchange(
        self, response: HttpResponse, body: bytes = b'', *, case: str = '',
        semantic_errors: frozenset = frozenset(),
        semantic_successes: frozenset = frozenset(),
    ) -> None:
        request = response.wsgi_request
        method = request.method.lower()
        if request.path in (
            '/api/schema/', '/api/docs/',
        ):
            return
        if response.status_code == 404 and not getattr(
            request, 'resolver_match', None,
        ):
            # URL resolver failures are not responses from an API operation.
            return
        for _path, pattern, _item in self.routes:
            match = pattern.fullmatch(request.path)
            if match:
                path, item = _path, _item
                break
        else:
            # Admin, index and deliberately unknown URLs are not API calls.
            callback = getattr(request.resolver_match, 'func', None)
            assert not hasattr(callback, 'cls'), request.path
            return
        if method == 'options' and 'options' not in item:
            return
        operation = item.get(method)
        implicit_head = method == 'head' and operation is None
        if implicit_head:
            operation = item.get('get')
        if operation is None and response.status_code == 405:
            # A rejected, unadvertised method is not a schema operation.
            return
        assert operation is not None, f'Undocumented {method.upper()} {path}'
        context = f'{method.upper()} {request.path}: {response.status_code}'
        responses = operation['responses']
        definition = responses.get(
            str(response.status_code),
            responses.get(f'{response.status_code // 100}XX',
                          responses.get('default')),
        )
        assert definition is not None, f'{context}: undocumented status'
        definition = self.resolve(definition)
        for name, entry in definition.get('headers', {}).items():
            header = self.resolve(entry)
            if not response.has_header(name):
                assert not header.get('required'), f'{context}: missing {name}'
                continue
            schema = header.get('schema', {})
            self.validate(schema, self.scalar(response[name], schema),
                          response=True)
        value = None
        if method != 'head':
            value = self.response_body(response, definition, context)
        # Negative tests and redirects may deliberately send invalid input.
        if 200 <= response.status_code < 300 and (
            path, method,
        ) not in semantic_errors:
            self.request_parameters(
                [*item.get('parameters', []),
                 *operation.get('parameters', [])],
                match.groupdict(), request,
            )
            self.request_body(operation, request, body)
        if implicit_head:
            return
        rows = value.get('results') if isinstance(value, dict) else value
        pagination = None
        if (
            200 <= response.status_code < 300
            and method == 'get' and self.is_paginated(operation)
            and isinstance(rows, list) and rows
        ):
            if 'limit' not in request.GET:
                pagination = 'default'
            elif request.GET['limit'] == '1':
                pagination = 'limit=1'
        outcome = 'unclassified'
        if response.status_code >= 400 or (path, method) in semantic_errors:
            outcome = 'error'
        elif (path, method) not in SEMANTIC_ERRORS or (
            path, method,
        ) in semantic_successes:
            outcome = 'success'
        self.observations.append({
            'path': path, 'method': method, 'status': response.status_code,
            'pagination': pagination, 'case': case, 'outcome': outcome,
        })

    def is_paginated(self, operation: dict) -> bool:
        def envelope(schema: dict) -> bool:
            schema = self.resolve(schema)
            if {'count', 'next', 'previous', 'results'} <= set(
                schema.get('properties', {}),
            ):
                return True
            return any(
                envelope(child) for key in ('oneOf', 'anyOf', 'allOf')
                for child in schema.get(key, [])
            )

        return any(
            envelope(media.get('schema', {}))
            for status, entry in operation['responses'].items()
            if status.startswith('2')
            for media in self.resolve(entry).get('content', {}).values()
        )

    def response_body(
        self, response: HttpResponse, definition: dict, context: str,
    ) -> Any:
        content = definition.get('content', {})
        if not content:
            assert not response.streaming, f'{context}: unexpected stream'
            assert not response.content, f'{context}: unexpected response body'
            return None
        media = self.media(content, response.get('Content-Type', ''))
        schema = media.get('schema', {})
        if response.streaming:
            assert schema.get('format') == 'binary', context
            return None
        value = (
            json.loads(response.content)
            if 'json' in response.get('Content-Type', '')
            else response.content
        )
        self.validate(schema, value, response=True)
        return value

    def request_parameters(
        self, parameters: list, path_values: dict, request: Any,
    ) -> None:
        sources = {
            'path': path_values, 'query': request.GET,
            'header': request.headers, 'cookie': request.COOKIES,
        }
        for entry in parameters:
            parameter = self.resolve(entry)
            source = sources[parameter['in']]
            name = parameter['name']
            if name not in source:
                assert not parameter.get('required'), f'Missing {name}'
                continue
            schema = self.resolve(parameter.get('schema', {}))
            value = source[name]
            if schema.get('type') == 'array':
                value = (
                    source.getlist(name)
                    if parameter.get('explode', True)
                    and hasattr(source, 'getlist') else value.split(',')
                )
                value = [self.scalar(v, schema['items']) for v in value]
            else:
                value = self.scalar(value, schema)
            self.validate(schema, value, response=False)

    @staticmethod
    def scalar(value: str, schema: dict) -> Any:
        kind = schema.get('type')
        if kind == 'integer' and re.fullmatch(r'[+-]?\d+', value):
            return int(value)
        if kind == 'number':
            try:
                return float(value)
            except ValueError:
                return value
        if kind == 'boolean' and value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        return value

    def request_body(self, operation: dict, request: Any, body: bytes) -> None:
        if 'requestBody' not in operation:
            return
        definition = self.resolve(operation['requestBody'])
        if not body:
            assert not definition.get('required'), 'Missing request body'
            return
        media = self.media(definition['content'], request.content_type)
        if 'json' in request.content_type:
            value = json.loads(body)
        elif request.content_type in (
            'multipart/form-data', 'application/x-www-form-urlencoded',
        ):
            value = self.form_body(request, body, media.get('schema', {}))
        else:
            value = body
        self.validate(media.get('schema', {}), value, response=False)

    def form_body(self, request: Any, body: bytes, schema: dict) -> dict:
        """Parse a copy so contract checks never consume the real request."""
        files = {}
        if request.content_type == 'multipart/form-data':
            values, files = MultiPartParser(
                request.META, BytesIO(body), [MemoryFileUploadHandler()],
            ).parse()
        else:
            values = QueryDict(body, encoding='utf-8')
        properties = self.resolve(schema).get('properties', {})
        result = {}
        for name in values:
            field = self.resolve(properties.get(name, {}))
            if field.get('type') == 'array':
                result[name] = [
                    self.scalar(value, field.get('items', {}))
                    for value in values.getlist(name)
                ]
            else:
                result[name] = self.scalar(values[name], field)
        for name, upload in files.items():
            result[name] = upload.read()
            upload.close()
        return result
