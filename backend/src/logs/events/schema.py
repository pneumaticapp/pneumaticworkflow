import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlsplit, urlunsplit

from django.core.serializers.json import DjangoJSONEncoder

from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    actor_type_from_auth,
)
from src.logs.events.reporting import report_error
from src.utils.logging import SentryLogLevel

TS_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
TS_SUFFIX = 'Z'

PAYLOAD_STR_MAX = 2000
PAYLOAD_MAX_BYTES = 32768
PAYLOAD_MAX_DEPTH = 2
REDACTED_VALUE = '[redacted]'
SECRET_KEY_PARTS = (
    'password',
    'passwd',
    'pwd',
    'token',
    'apikey',
    'secret',
    'authorization',
    'credential',
    'private',
    'cookie',
    'session',
    'signature',
    'salt',
    'bearer',
    'jwt',
    'otp',
    'refresh',
)
NOT_ALPHANUMERIC = re.compile(r'[^a-z0-9]')
QUERY_MARK = '?'


def format_ts(value: datetime) -> str:

    """ Serialize a moment as RFC3339 UTC with microseconds.
        A naive value is treated as UTC: the project stores
        aware datetimes, so naive means a hand made value. """

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime(TS_FORMAT) + TS_SUFFIX


def parse_ts(value: str) -> datetime:

    """ Read back the value produced by format_ts. """

    # A slice, not rstrip: rstrip strips a set of characters and
    # would eat as many trailing suffix letters as it finds.
    return datetime.strptime(
        value[:-len(TS_SUFFIX)], TS_FORMAT,
    ).replace(tzinfo=timezone.utc)


@dataclass
class Actor:

    type: ActorType.LITERALS
    id: Optional[int] = None
    email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'id': self.id,
            'email': self.email,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional['Actor']:
        if not data:
            return None
        return cls(
            type=data['type'],
            id=data.get('id'),
            email=data.get('email'),
        )

    @classmethod
    def from_user(
        cls,
        user,
        auth_type: Optional[str] = None,
    ) -> 'Actor':

        """ The person behind a request or a service call. The
            auth type tells a browser session from an API key; a
            service that does not know it is a user session. """

        return cls(
            type=actor_type_from_auth(auth_type or AuthTokenType.USER),
            id=user.id,
            email=user.email,
        )


@dataclass
class EventObject:

    type: str
    id: Optional[Union[int, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'id': self.id,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional['EventObject']:
        if not data:
            return None
        return cls(
            type=data['type'],
            id=data.get('id'),
        )


@dataclass
class Event:

    type: str
    category: EventCategory.LITERALS
    ts: datetime
    account_id: int
    actor: Optional[Actor] = None
    object: Optional[EventObject] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    # What the registry declared as personal data when the event was
    # built. The sink does not read it back from the record: it asks
    # the registry again, so a hand written record cannot hide a
    # field from the pii.* namespace. Kept for reading a record of
    # the stream by eye and for the audit answer "what left".
    pii: Tuple[str, ...] = ()
    # Which service wrote the record: the OTLP resource service.name.
    # None is a record of the backend written before the field
    # existed, the sink puts its own name there (P3 of the file
    # service design).
    service: Optional[str] = None
    workflow_id: Optional[int] = None
    task_id: Optional[int] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    # Stream id, known only after the record is read back
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:

        """ The id is written only when it is known: a record of the
            stream carries none, Redis assigns it on XADD and the
            reader puts it back. """

        data: Dict[str, Any] = {
            'type': self.type,
            'category': self.category,
            'service': self.service,
            'ts': format_ts(self.ts),
            'account_id': self.account_id,
            'actor': self.actor.to_dict() if self.actor else None,
            'object': self.object.to_dict() if self.object else None,
            'workflow_id': self.workflow_id,
            'task_id': self.task_id,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'request_id': self.request_id,
            'payload': self.payload,
            'pii': list(self.pii),
        }
        if self.id is not None:
            data['id'] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        return cls(
            type=data['type'],
            category=data['category'],
            ts=parse_ts(data['ts']),
            account_id=data['account_id'],
            actor=Actor.from_dict(data.get('actor')),
            object=EventObject.from_dict(data.get('object')),
            payload=data.get('payload') or {},
            pii=tuple(data.get('pii') or ()),
            service=data.get('service'),
            workflow_id=data.get('workflow_id'),
            task_id=data.get('task_id'),
            ip=data.get('ip'),
            user_agent=data.get('user_agent'),
            request_id=data.get('request_id'),
            id=data.get('id'),
        )


def normalize_payload(payload: Optional[dict]) -> dict:

    """ Make a payload safe to store and to send:
        no secrets, no deep nesting, no huge strings.
        An oversized payload is replaced by its size marker: a single
        event must not be able to fill up the stream. """

    if not payload:
        return {}
    normalized = _normalize_dict(payload, depth=1)
    size = len(to_json(normalized).encode('utf-8'))
    if size > PAYLOAD_MAX_BYTES:

        # Losing the payload of an audit event is worth a report: the
        # size marker alone leaves the operator with an event nobody
        # can explain. Throttled, an emitter loop would flood Sentry.
        report_error(
            'Event payload dropped: over the size limit',
            {'size': size, 'limit': PAYLOAD_MAX_BYTES},
            level=SentryLogLevel.WARNING,
        )
        return {'_truncated': True, '_size': size}
    return normalized


def _normalize_dict(value: dict, depth: int) -> Dict[str, Any]:
    normalized = {}
    for key, item in value.items():
        name = str(key)
        if _is_secret_key(name):
            normalized[name] = REDACTED_VALUE
        else:
            normalized[name] = _normalize_value(item, depth)
    return normalized


def _normalize_value(value: Any, depth: int) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return without_query(value)[:PAYLOAD_STR_MAX]
    if isinstance(value, dict):
        if depth >= PAYLOAD_MAX_DEPTH:
            return _to_json_value(value)
        return _normalize_dict(value, depth + 1)
    if isinstance(value, (list, tuple, set, frozenset)):
        if depth >= PAYLOAD_MAX_DEPTH:
            return _to_json_value(value)
        return [_normalize_value(item, depth + 1) for item in value]
    return _to_scalar(value)


def _is_secret_key(name: str) -> bool:

    """ Compare the name without separators and case: api_key,
        api-key, X-API-Key and apiKey are one and the same key. """

    normalized = NOT_ALPHANUMERIC.sub('', name.lower())
    return any(part in normalized for part in SECRET_KEY_PARTS)


def without_query(value: str) -> str:

    """ Cut the query string off a URL value: access tokens and
        signatures ride there ("...?access_token=abc").
        Anything that is not an absolute URL is left alone: a plain
        string may hold a question mark for its own reasons. """

    if QUERY_MARK not in value:
        return value
    try:
        parts = urlsplit(value)
    except ValueError:
        return value
    if not (parts.scheme and parts.netloc and parts.query):
        return value
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, '', parts.fragment),
    )


def _to_scalar(value: Any) -> Any:

    """ Convert a non JSON type the way DjangoJSONEncoder does. """

    try:
        return DjangoJSONEncoder().default(value)
    except TypeError:
        return str(value)[:PAYLOAD_STR_MAX]


def _to_json_value(value: Any) -> str:

    """ Collapse a too deep container into a JSON string,
        keeping secrets redacted at any depth. """

    return to_json(_redact(value))[:PAYLOAD_STR_MAX]


def to_json(value: Any) -> str:

    """ JSON of anything, used by the payload size check and by the
        OTLP sink: a value that cannot be encoded becomes its repr
        instead of breaking the whole batch. """

    try:
        return json.dumps(value, cls=DjangoJSONEncoder)
    except (TypeError, ValueError):
        return json.dumps(str(value))


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return without_query(value)
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED_VALUE if _is_secret_key(str(key))
                else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_redact(item) for item in value]
    return value
