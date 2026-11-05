"""OpenAPI 3.1 assertions for HTTP exchanges and complete Files coverage."""

import json
import re
from email import policy
from email.parser import BytesParser
from fnmatch import fnmatchcase
from ipaddress import AddressValueError, IPv6Address
from typing import Any

import httpx
from jsonschema import Draft202012Validator, FormatChecker

HTTP_METHODS = {
    'get',
    'post',
    'put',
    'patch',
    'delete',
    'head',
    'options',
    'trace',
}


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


class FilesContract:
    """Validate actual client exchanges, never constructed HTTP responses."""

    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.observed: set[tuple[str, str, int]] = set()
        self.routes = []
        for path, item in sorted(
            document['paths'].items(),
            key=lambda pair: pair[0].count('{'),
        ):
            pattern = re.escape(path)
            for name in re.findall(r'\{([^}]+)\}', path):
                pattern = pattern.replace(
                    re.escape('{' + name + '}'),
                    f'(?P<{name}>[^/]+)',
                )
            self.routes.append((path, re.compile(pattern + '$'), item))

    def resolve(self, value: dict[str, Any]) -> dict[str, Any]:
        while '$ref' in value:
            reference = value['$ref']
            assert reference.startswith('#/'), 'Only local references allowed'
            value = self.document
            for part in reference[2:].split('/'):
                value = value[part.replace('~1', '/').replace('~0', '~')]
        return value

    def validate(self, schema: dict[str, Any], value: Any) -> None:
        # The wrapper keeps local component references rooted in the full
        # document, while the fragment applies only to the supplied value.
        root = {
            'allOf': [schema],
            'components': self.document.get('components', {}),
        }
        formats = FormatChecker()
        formats.checks('uri')(_is_uri)
        Draft202012Validator(root, format_checker=formats).validate(
            value,
        )

    @staticmethod
    def media(content: dict, content_type: str) -> dict:
        mime = content_type.partition(';')[0].lower()
        for pattern, definition in sorted(content.items(), reverse=True):
            if fnmatchcase(mime, pattern):
                return definition
        message = f'Undocumented Content-Type: {mime}'
        raise AssertionError(message)

    @staticmethod
    def scalar(value: str, schema: dict) -> Any:
        if schema.get('type') == 'integer' and re.fullmatch(r'\d+', value):
            return int(value)
        return value

    def exchange(self, response: httpx.Response) -> None:
        request = response.request
        method = request.method.lower()
        public_path = request.url.path
        if not public_path.startswith('/files/'):
            public_path = '/files' + public_path
        for path, pattern, item in self.routes:
            match = pattern.fullmatch(public_path)
            if match and method in item:
                self.operation(response, path, method, item, match.groupdict())
                return
        message = f'Undocumented operation: {method.upper()} {public_path}'
        raise AssertionError(message)

    def operation(
        self,
        response: httpx.Response,
        path: str,
        method: str,
        item: dict,
        path_values: dict[str, str],
    ) -> None:
        operation = item.get(method)
        assert operation is not None, f'Undocumented {method.upper()} {path}'
        status = response.status_code
        definition = operation['responses'].get(str(status))
        assert definition is not None, f'{method.upper()} {path}: {status}'
        definition = self.resolve(definition)
        for name, header in definition.get('headers', {}).items():
            # These are the headers promised for this response by the API.
            assert name in response.headers, f'{status}: missing {name}'
            schema = self.resolve(header).get('schema', {})
            self.validate(schema, self.scalar(response.headers[name], schema))
        content = definition.get('content', {})
        if not content:
            assert response.content == b'', f'{status}: unexpected body'
        else:
            media = self.media(
                content,
                response.headers.get('Content-Type', ''),
            )
            schema = media.get('schema', {})
            if schema.get('format') == 'binary':
                assert isinstance(response.content, bytes)
                assert len(response.content) == int(
                    response.headers['Content-Length'],
                )
            else:
                self.validate(schema, response.json())
        if 200 <= status < 300:
            self.request(operation, response.request, path_values)
        self.observed.add((path, method, status))

    def request(
        self,
        operation: dict,
        request: httpx.Request,
        path_values: dict[str, str],
    ) -> None:
        sources = {
            'path': path_values,
            'header': request.headers,
            'query': request.url.params,
        }
        for entry in operation.get('parameters', []):
            parameter = self.resolve(entry)
            source = sources[parameter['in']]
            name = parameter['name']
            if name not in source:
                assert not parameter.get('required'), f'Missing {name}'
                continue
            schema = parameter.get('schema', {})
            self.validate(schema, self.scalar(source[name], schema))
        definition = operation.get('requestBody')
        if not definition:
            return
        definition = self.resolve(definition)
        assert request.content or not definition.get('required')
        if not request.content:
            return
        mime = request.headers.get('Content-Type', '')
        media = self.media(definition['content'], mime)
        schema = self.resolve(media.get('schema', {}))
        if mime.startswith('multipart/form-data'):
            binary_fields = frozenset(
                name
                for name, field in schema.get('properties', {}).items()
                if self.resolve(field).get('format') == 'binary'
            )
            value = self.multipart(request, binary_fields)
        else:
            value = json.loads(request.content)
        self.validate(schema, value)

    @staticmethod
    def multipart(
        request: httpx.Request,
        binary_fields: frozenset[str] = frozenset(),
    ) -> dict[str, str]:
        headers = (
            f'Content-Type: {request.headers["Content-Type"]}\r\n\r\n'
        ).encode()
        message = BytesParser(policy=policy.default).parsebytes(
            headers + request.content,
        )
        assert message.is_multipart(), 'Invalid multipart body'
        values = {}
        file_parts = set()
        for part in message.iter_parts():
            name = part.get_param('name', header='content-disposition')
            assert name is not None, 'Multipart parts must include a name'
            payload = part.get_payload(decode=True)
            assert isinstance(payload, bytes)
            filename = part.get_param('filename', header='content-disposition')
            if filename is not None:
                file_parts.add(name)
                # A one-to-one representation of the wire bytes for the
                # OAS binary string; the HTTP parser still sees raw bytes.
                values[name] = payload.decode('latin-1')
            else:
                file_parts.discard(name)
                values[name] = payload.decode('utf-8')
        missing_files = binary_fields.intersection(values).difference(
            file_parts,
        )
        assert not missing_files, 'File fields must include a filename'
        return values

    def assert_complete(self) -> None:
        expected = {
            (path, method, int(status))
            for path, item in self.document['paths'].items()
            for method, operation in item.items()
            if method in HTTP_METHODS
            for status in operation['responses']
        }
        missing = sorted(expected - self.observed)
        assert not missing, f'Files contracts lack HTTP coverage: {missing}'
        for _path, _pattern, item in self.routes:
            for method, operation in item.items():
                if method not in HTTP_METHODS:
                    continue
                assert not any(
                    parameter['in'] == 'query'
                    and parameter['name'] in {'limit', 'offset', 'page'}
                    for parameter in operation.get('parameters', [])
                ), 'Files API has no pagination'

    def report(self) -> dict[str, Any]:
        return {
            'openapi': self.document['openapi'],
            'operations': sum(
                method in HTTP_METHODS
                for _path, _pattern, item in self.routes
                for method in item
            ),
            'observed': [
                {'path': path, 'method': method, 'status': status}
                for path, method, status in sorted(self.observed)
            ],
            'pagination': 'not_applicable: upload and binary retrieval',
        }
