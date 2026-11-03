from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from src.accounts.enums import UserType
from src.logs.events.enums import EventCategory

TS_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
TS_SUFFIX = 'Z'


def format_ts(value: datetime) -> str:
    """Serialize a moment as RFC3339 UTC with microseconds.
    A naive value is treated as UTC: the project stores
    aware datetimes, so naive means a hand made value."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime(TS_FORMAT) + TS_SUFFIX


@dataclass
class Actor:
    """The person who acted: a user of the account or a guest of
    one task. Nobody, the system, is no actor at all: the actor
    of the record is then null. How the person was authenticated
    is not part of the actor, it is Event.auth_type."""

    id: Optional[int] = None
    email: Optional[str] = None
    user_type: Optional[UserType.LITERALS] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'email': self.email,
            'user_type': self.user_type,
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional['Actor']:
        if not data:
            return None
        return cls(
            id=data.get('id'),
            email=data.get('email'),
            user_type=data.get('user_type'),
        )


@dataclass
class EventObject:
    type: str
    id: Optional[Union[int, str]] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {'type': self.type, 'id': self.id}
        if self.name is not None:
            data['name'] = self.name
        return data

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional['EventObject']:
        if not data:
            return None
        return cls(type=data['type'], id=data.get('id'), name=data.get('name'))


@dataclass
class Event:
    type: str
    category: EventCategory.LITERALS
    ts: datetime
    account_id: int
    actor: Optional[Actor] = None
    account_name: Optional[str] = None
    auth_type: Optional[str] = None
    object: Optional[EventObject] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    service: str = ''
    workflow_id: Optional[int] = None
    task_id: Optional[int] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """The id is written only when it is known: a record of the
        stream carries none, Redis assigns it on XADD and the
        reader puts it back."""
        data: Dict[str, Any] = {
            'type': self.type,
            'category': self.category,
            'service': self.service,
            'ts': format_ts(self.ts),
            'account_id': self.account_id,
            'actor': self.actor.to_dict() if self.actor else None,
            'auth_type': self.auth_type,
            'object': self.object.to_dict() if self.object else None,
            'workflow_id': self.workflow_id,
            'task_id': self.task_id,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'request_id': self.request_id,
            'payload': self.payload,
        }
        if self.id is not None:
            data['id'] = self.id
        if self.account_name is not None:
            data['account_name'] = self.account_name
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        """ts is read back from the value format_ts produced."""
        ts = datetime.strptime(
            data['ts'][: -len(TS_SUFFIX)],
            TS_FORMAT,
        ).replace(tzinfo=timezone.utc)
        return cls(
            type=data['type'],
            category=data['category'],
            ts=ts,
            account_id=data['account_id'],
            actor=Actor.from_dict(data.get('actor')),
            auth_type=data.get('auth_type'),
            object=EventObject.from_dict(data.get('object')),
            payload=data.get('payload') or {},
            service=data['service'],
            workflow_id=data.get('workflow_id'),
            task_id=data.get('task_id'),
            ip=data.get('ip'),
            user_agent=data.get('user_agent'),
            request_id=data.get('request_id'),
            id=data.get('id'),
            account_name=data.get('account_name'),
        )


Entries = List[Tuple[str, Event]]
RawEntries = List[Tuple[str, dict]]


@dataclass
class ParsedEntries:
    """What one answer of Redis holds.

    Three kinds of entries come back besides the good ones, all
    after the stream was trimmed past records that were still
    pending: XAUTOCLAIM of Redis 6.2 answers a deleted record as
    a (None, None) pair, XREADGROUP answers it as an id with no
    fields. Both are gone for good, nothing can be delivered or
    parked: the id, when there is one, is acked and the pair is
    dropped. A record that is there but cannot be parsed goes to
    the dead letter. next_cursor preserves the XAUTOCLAIM scan position;
    '0-0' means the scan reached the end of the pending list."""

    events: Entries = field(default_factory=list)
    malformed: RawEntries = field(default_factory=list)
    vanished: List[str] = field(default_factory=list)
    next_cursor: str = '0-0'


@dataclass
class ConsumerStats:
    """Result of a single tick, also the source of the log line.
    failed is read by the beat task: a batch left pending after
    every attempt is a delivery outage worth a Sentry message.
    So are vanished (records trimmed off the stream while they
    were pending, that is lost) and malformed (records parked in
    the dead letter because they are not events)."""

    delivered: int = 0
    acked: int = 0
    dead: int = 0
    claimed: int = 0
    vanished: int = 0
    malformed: int = 0
    failed: bool = False
    duration_ms: int = 0


@dataclass
class TickBudget:
    """One budget for the whole tick, shared by its three phases: the
    limit counts batches and unfinished claim scans, and the deadline ends a
    tick that is slow rather than long."""

    batches: int
    deadline: float
    stopped: bool = False


@dataclass
class RequestContext:
    """Metadata of the HTTP request currently being handled."""

    request_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


request_context: ContextVar[Optional[RequestContext]] = ContextVar(
    'pneumatic_event_context',
    default=None,
)
