import json
import re
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model

from src.utils.logging import SentryLogLevel, capture_sentry_message_throttled

PAYLOAD_STR_MAX = 2000
PAYLOAD_MAX_BYTES = 65536
PAYLOAD_MAX_DEPTH = 2
FIRST_DEPTH = 1
NO_DEPTH_LIMIT = None
REDACTED_VALUE = '[redacted]'
TRUNCATED_KEY = '_truncated'
PAYLOAD_SCALAR_TYPES = (str, int, float, bool)
SIZE_KEY = '_size'
SECRET_KEY_PARTS = (
    'password',
    'passwd',
    'apikey',
    'token',
    'secret',
    'authorization',
    'credential',
    'cookie',
    'signature',
    'bearer',
    'jwt',
    'privatekey',
    'sessionid',
    'sessionkey',
)
SECRET_KEY_WORDS = ('pwd', 'otp', 'salt')
SECRET_KEY_NAMES = ('session', 'refresh', 'access', 'private')
KEY_WORD = re.compile('[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])')
NOT_ALPHANUMERIC = re.compile('[^a-z0-9]')
QUERY_MARK = '?'
USERINFO_MARK = '@'


def normalize_payload(payload: Optional[dict]) -> dict:
    """Make a payload safe to store and to send:
    no secrets, no deep nesting, no huge strings.

    An oversized payload is cut down to its size marker with the
    scalars of the top level: a single event must not be able to
    fill up the stream, and the name or the is_active of a template
    are what a dashboard filters the events by, while the lists and
    the dicts next to them - the tasks and the fields of the
    template - make a payload big. Every string is already cut to
    PAYLOAD_STR_MAX. When the scalars alone are over the limit too,
    only the marker is left."""
    if not payload:
        return {}
    normalized = _normalize_dict(value=payload, depth=FIRST_DEPTH)
    size = len(to_json(normalized).encode('utf-8'))
    if size <= PAYLOAD_MAX_BYTES:
        return normalized
    capture_sentry_message_throttled(
        message='Event payload dropped: over the size limit',
        data={'size': size, 'limit': PAYLOAD_MAX_BYTES},
        level=SentryLogLevel.WARNING,
    )
    truncated = {
        name: value
        for name, value in normalized.items()
        if value is None or isinstance(value, PAYLOAD_SCALAR_TYPES)
    }
    truncated[TRUNCATED_KEY] = True
    truncated[SIZE_KEY] = size
    if len(to_json(truncated).encode('utf-8')) > PAYLOAD_MAX_BYTES:
        return {TRUNCATED_KEY: True, SIZE_KEY: size}
    return truncated


def _normalize_dict(value: dict, depth: Optional[int]) -> Dict[str, Any]:
    """Compare a key without separators and case: api_key, api-key,
    X-API-Key and apiKey are one and the same key."""
    normalized = {}
    for key, item in value.items():
        name = str(key)
        compact_name = NOT_ALPHANUMERIC.sub('', name.lower())
        words = {word.lower() for word in KEY_WORD.findall(name)}
        if (
            compact_name in SECRET_KEY_NAMES
            or any(part in compact_name for part in SECRET_KEY_PARTS)
            or any(word in words for word in SECRET_KEY_WORDS)
        ):
            normalized[name] = REDACTED_VALUE
        else:
            normalized[name] = _normalize_value(value=item, depth=depth)
    return normalized


def _normalize_value(value: Any, depth: Optional[int]) -> Any:
    """One pass over the payload: secrets out, credentials and query
    strings off urls, long strings cut, unknown types stringified.

    depth is NO_DEPTH_LIMIT inside a container that is being
    collapsed into a JSON string: whatever it holds ends up in
    that one string, so there is nothing left to collapse."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return without_url_secrets(value)[:PAYLOAD_STR_MAX]
    next_depth = None if depth is None else depth + 1
    if isinstance(value, dict):
        if depth is not None and depth >= PAYLOAD_MAX_DEPTH:
            return to_json(_normalize_dict(value=value, depth=NO_DEPTH_LIMIT))
        return _normalize_dict(value=value, depth=next_depth)
    if isinstance(value, (list, tuple, set, frozenset)):
        if depth is not None and depth >= PAYLOAD_MAX_DEPTH:
            return to_json(
                [
                    _normalize_value(value=item, depth=NO_DEPTH_LIMIT)
                    for item in value
                ],
            )
        return [
            _normalize_value(value=item, depth=next_depth) for item in value
        ]
    if isinstance(value, Model):
        return {
            'id': value.pk,
            'name': without_url_secrets(str(value))[:PAYLOAD_STR_MAX],
        }
    try:
        return DjangoJSONEncoder().default(value)
    except TypeError:
        return str(value)[:PAYLOAD_STR_MAX]


def without_url_secrets(value: str) -> str:
    """Cut the credential and the query string off a URL value: a
    password rides in the authority ("https://user:pass@host"),
    access tokens and signatures in the query ("...?token=abc").
    Anything that is not an absolute URL is left alone: a plain
    string may hold a question mark or an at sign for its own
    reasons, an e-mail address above all. The host and the port
    are kept as written, an IPv6 host with its brackets."""
    if QUERY_MARK not in value and USERINFO_MARK not in value:
        return value
    try:
        parts = urlsplit(value)
    except ValueError:
        return value
    if not (parts.scheme and parts.netloc):
        return value
    if USERINFO_MARK not in parts.netloc and (not parts.query):
        return value
    return urlunsplit(
        parts._replace(
            netloc=parts.netloc.rpartition(USERINFO_MARK)[2],
            query='',
        ),
    )


def to_json(value: Any) -> str:
    """JSON of anything, used by the payload size check and by the
    OTLP sink: a value that cannot be encoded becomes its repr
    instead of breaking the whole batch. A value the pipeline built
    itself is dumped with json.dumps directly: there a value that
    cannot be encoded is a bug, and it has to be seen."""
    try:
        return json.dumps(value, cls=DjangoJSONEncoder)
    except (TypeError, ValueError):
        return json.dumps(str(value))
