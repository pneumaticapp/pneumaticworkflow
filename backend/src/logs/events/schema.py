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
FIRST_DEPTH = 1
# Depth of a value inside a container that is collapsed into a JSON
# string: nothing below it can be collapsed any further.
NO_DEPTH_LIMIT = None
REDACTED_VALUE = '[redacted]'
TRUNCATED_KEY = '_truncated'
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
KEY_WORD = re.compile(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])')
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
    # Every writer fills it, the sink groups records by it.
    service: str = ''
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
            service=data['service'],
            workflow_id=data.get('workflow_id'),
            task_id=data.get('task_id'),
            ip=data.get('ip'),
            user_agent=data.get('user_agent'),
            request_id=data.get('request_id'),
            id=data.get('id'),
        )


PII_ROOTS = ('ip', 'user_agent')
PII_NAMESPACES = ('actor', 'object', 'payload')


def split_pii_path(path: str) -> Tuple[str, str]:

    """ Split a personal data path into its head and its tail.

        A path names a field of a record: a root of the record itself
        ("ip"), or a key inside one of its namespaces
        ("actor.email", "payload.filename"). The registry validating
        a declaration and the emitter filling Event.pii both split
        them here; the sink matches whole paths against attribute
        keys named after them (otlp_payload._extract_pii).
    """

    head, _, tail = path.partition('.')
    return head, tail


def is_valid_pii_path(path: str) -> bool:

    """ Whether a path can name a field at all.

        An unresolvable path is dropped without a word and the field
        then leaves as a plain attribute past the redaction rule of
        the collector, so a typo is a silent data leak.
    """

    head, tail = split_pii_path(path)
    if head in PII_ROOTS:
        return not tail
    return head in PII_NAMESPACES and bool(tail)


def pii_value(event: 'Event', path: str) -> Any:

    """ The value a valid personal data path points at, or None. """

    head, tail = split_pii_path(path)
    if head == 'payload':
        return event.payload.get(tail)
    if head in ('actor', 'object'):
        holder = getattr(event, head, None)
        return getattr(holder, tail, None) if holder else None
    if tail:
        return None
    return getattr(event, head, None)


def normalize_payload(payload: Optional[dict]) -> dict:

    """ Make a payload safe to store and to send:
        no secrets, no deep nesting, no huge strings.
        An oversized payload is replaced by its size marker: a single
        event must not be able to fill up the stream. """

    if not payload:
        return {}
    normalized = _normalize_dict(payload, depth=FIRST_DEPTH)
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
        return {TRUNCATED_KEY: True, SIZE_KEY: size}
    return normalized


def _normalize_dict(value: dict, depth: Optional[int]) -> Dict[str, Any]:
    normalized = {}
    for key, item in value.items():
        name = str(key)
        if _is_secret_key(name):
            normalized[name] = REDACTED_VALUE
        else:
            normalized[name] = _normalize_value(item, depth)
    return normalized


def _normalize_value(value: Any, depth: Optional[int]) -> Any:

    """ One pass over the payload: secrets out, query strings off,
        long strings cut, unknown types stringified.

        depth is NO_DEPTH_LIMIT inside a container that is being
        collapsed into a JSON string: whatever it holds ends up in
        that one string, so there is nothing left to collapse. """

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return without_query(value)[:PAYLOAD_STR_MAX]
    if isinstance(value, dict):
        if _too_deep(depth):
            return _collapse(_normalize_dict(value, NO_DEPTH_LIMIT))
        return _normalize_dict(value, _deeper(depth))
    if isinstance(value, (list, tuple, set, frozenset)):
        if _too_deep(depth):
            return _collapse([
                _normalize_value(item, NO_DEPTH_LIMIT) for item in value
            ])
        return [_normalize_value(item, _deeper(depth)) for item in value]
    return _to_scalar(value)


def _too_deep(depth: Optional[int]) -> bool:
    return depth is not None and depth >= PAYLOAD_MAX_DEPTH


def _deeper(depth: Optional[int]) -> Optional[int]:

    """ Depth of the values inside a container. NO_DEPTH_LIMIT stays
        itself: inside a container that is being collapsed the whole
        subtree goes into one string, however deep it is. """

    if depth is NO_DEPTH_LIMIT:
        return NO_DEPTH_LIMIT
    return depth + 1


def _collapse(value: Any) -> str:

    """ A container deeper than PAYLOAD_MAX_DEPTH becomes one
        attribute of the record instead of a tree the log backend
        would index field by field.

        The value is normalized before it is dumped, not after: a
        JSON string cut to PAYLOAD_STR_MAX would end mid-escape and
        arrive at the backend as broken JSON. Normalizing first also
        bounds the result, since every string inside is cut, and
        PAYLOAD_MAX_BYTES bounds the payload as a whole. """

    return to_json(value)


def _is_secret_key(name: str) -> bool:

    """ Compare the name without separators and case: api_key,
        api-key, X-API-Key and apiKey are one and the same key. """

    normalized = NOT_ALPHANUMERIC.sub('', name.lower())
    if normalized in SECRET_KEY_NAMES:
        return True
    if any(part in normalized for part in SECRET_KEY_PARTS):
        return True
    words = {word.lower() for word in KEY_WORD.findall(name)}
    return any(word in words for word in SECRET_KEY_WORDS)


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


def dump_json(value: Any) -> str:

    """ JSON of a value the pipeline built itself.

        Raises on a value that cannot be encoded: in a stream record or
        an OTLP body that is a bug, and it has to be seen. to_json is
        the lenient sibling for values that come from outside. """

    return json.dumps(value, cls=DjangoJSONEncoder)


def to_json(value: Any) -> str:

    """ JSON of anything, used by the payload size check and by the
        OTLP sink: a value that cannot be encoded becomes its repr
        instead of breaking the whole batch. """

    try:
        return dump_json(value)
    except (TypeError, ValueError):
        return json.dumps(str(value))
