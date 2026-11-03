import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from django.conf import settings

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.entities import Actor, Event, EventObject, ParsedEntries
from src.logs.events.enums import (
    AccountEvents,
    AdminEvents,
    ApiKeyEvents,
    BillingEvents,
    DatasetEvents,
    EventCategory,
    FileEvents,
    GroupEvents,
    TaskEvents,
    TemplateEvents,
    UserEvents,
    WebhookEvents,
    WorkflowEvents,
)
from src.logs.events.stream import (
    AUTOCLAIM_START,
    DEAD_MAXLEN,
    NEW_ENTRIES,
    EventStream,
)

Entries = List[Tuple[str, Event]]
EVENT_TS = datetime(2026, 9, 8, 10, 15, 30, 123456, tzinfo=timezone.utc)
SMOKE_ACCOUNT_ID = 7
UNIT_STREAM_URL = 'redis://localhost:6379/4'
UNIT_STREAM_KEY = 'pneumatic:events-unit'
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
EVENT_CLASSES = (
    WorkflowEvents,
    TaskEvents,
    UserEvents,
    AccountEvents,
    GroupEvents,
    ApiKeyEvents,
    TemplateEvents,
    DatasetEvents,
    BillingEvents,
    WebhookEvents,
    FileEvents,
    AdminEvents,
)


@dataclass
class PendingEntry:
    """One record of the pending entries list of the group."""

    entry_id: str
    event: Event
    consumer: str
    delivered_at: float = field(default_factory=monotonic)

    def idle_ms(self, now: float) -> float:
        return (now - self.delivered_at) * 1000


class FakeEventStream:
    """In memory EventStream for unit tests: same interface, same
    delivery semantics (a group with a per consumer pending list),
    no Redis. Time is monotonic, so idle is set by delivered_at."""

    def __init__(
        self,
        key: str = 'pneumatic:events',
        group: str = 'otlp',
        maxlen: int = 1000000,
    ):
        self.key = key
        self.group = group
        self.maxlen = maxlen
        self.events: Entries = []
        self.dead: List[Tuple[str, Any, str]] = []
        self.pending: Dict[str, PendingEntry] = {}
        self.group_created = False
        self._delivered = 0
        self._sequence = 0
        self._claim_cursors: Dict[str, str] = {}

    def xadd(self, event: Event) -> str:
        self._sequence += 1
        entry_id = f'{self._sequence}-0'
        stored = Event.from_dict(event.to_dict())
        stored.id = entry_id
        self.events.append((entry_id, stored))
        self._trim()
        return entry_id

    def ensure_group(self):
        self.group_created = True

    def read(self, consumer: str, count: int, start_id: str) -> ParsedEntries:
        if start_id != NEW_ENTRIES:
            now = monotonic()
            entries = []
            for entry in self._pending_of(consumer)[:count]:
                entry.delivered_at = now
                entries.append((entry.entry_id, entry.event))
            return ParsedEntries(events=entries)
        entries = self.events[self._delivered:self._delivered + count]
        self._delivered += len(entries)
        for entry_id, event in entries:
            self.pending[entry_id] = PendingEntry(entry_id, event, consumer)
        return ParsedEntries(events=list(entries))

    def autoclaim(
        self,
        consumer: str,
        min_idle_ms: int,
        count: int,
        start_id: Optional[str] = None,
    ) -> ParsedEntries:
        now = monotonic()
        if start_id is None:
            start_id = self._claim_cursors.get(consumer, AUTOCLAIM_START)
        pending = [
            entry
            for entry in self._sorted_pending()
            if int(entry.entry_id.split('-')[0]) >= int(start_id.split('-')[0])
        ]
        claimed = []
        scanned = 0
        for entry in pending[: count * 10]:
            scanned += 1
            if entry.idle_ms(now) < min_idle_ms:
                continue
            entry.consumer = consumer
            entry.delivered_at = now
            claimed.append((entry.entry_id, entry.event))
            if len(claimed) >= count:
                break
        cursor = (
            pending[scanned].entry_id
            if scanned < len(pending)
            else AUTOCLAIM_START
        )
        self._claim_cursors[consumer] = cursor
        return ParsedEntries(events=claimed, next_cursor=cursor)

    def ack(self, ids: Iterable[str]) -> int:
        acked = 0
        for entry_id in ids:
            if self.pending.pop(entry_id, None) is not None:
                acked += 1
        return acked

    def dead_letter(self, entries: List[Tuple[str, Any]], reason: str) -> int:
        for entry_id, event in entries:
            self.dead.append((entry_id, event, reason))
        del self.dead[:-DEAD_MAXLEN]
        return self.ack([entry_id for entry_id, _ in entries])

    def last_event(self) -> Optional[Event]:
        """Test helper: the event of the last xadd."""
        return self.events[-1][1] if self.events else None

    def _trim(self):
        extra = len(self.events) - self.maxlen
        if extra > 0:
            del self.events[:extra]
            self._delivered = max(self._delivered - extra, 0)

    def _pending_of(self, consumer: str) -> List[PendingEntry]:
        return [
            entry
            for entry in self._sorted_pending()
            if entry.consumer == consumer
        ]

    def _sorted_pending(self) -> List[PendingEntry]:
        return sorted(
            self.pending.values(),
            key=lambda entry: int(entry.entry_id.split('-')[0]),
        )

    def _consumers(self) -> set:
        return {entry.consumer for entry in self.pending.values()}


def make_event(**kwargs) -> Event:
    """Filled event of the 5.1 sample. Override only the fields the
    test is about, so an assertion reads as the difference."""
    fields: Dict[str, Any] = {
        'type': 'workflow.run',
        'category': EventCategory.WORKFLOWS,
        'service': settings.LOGS_SERVICE_NAME,
        'ts': EVENT_TS,
        'account_id': 42,
        'actor': Actor(
            id=17,
            email='ann@example.com',
            user_type=UserType.USER,
        ),
        'auth_type': AuthTokenType.USER,
        'object': EventObject(type='workflow', id=9001),
        'payload': {'template_id': 12},
        'workflow_id': 9001,
        'task_id': None,
        'ip': '203.0.113.7',
        'user_agent': 'Mozilla/5.0',
        'request_id': '3f9c2c1e6d0b4a0f9e2b7c1d5a6e8f90',
    }
    fields.update(kwargs)
    return Event(**fields)


def load_file_service_record(
    name: str = 'file_service_record.json',
) -> Dict[str, Any]:
    """A contract record as the consumer reads it off the stream.

    One file per event type the file service writes: the tests of
    the other writer compare what they build with the same file,
    so a rename on either side breaks both."""
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, encoding='utf-8') as fixture:
        return json.load(fixture)


def load_file_service_contract() -> Dict[str, Any]:
    """The names the two writers have to agree on besides the shape
    of a record: the stream both write into and the actor types
    the file service may put into a record."""
    path = os.path.join(FIXTURES_DIR, 'file_service_contract.json')
    with open(path, encoding='utf-8') as fixture:
        return json.load(fixture)


def make_smoke_event(number: int = 0) -> Event:
    """Smallest event the pipeline accepts."""
    return Event(
        type='system.smoke',
        category=EventCategory.ACCOUNTS,
        ts=EVENT_TS,
        account_id=SMOKE_ACCOUNT_ID,
        object=EventObject(type='account', id=SMOKE_ACCOUNT_ID),
        payload={'number': number},
    )


def fill_stream(stream, count: int = 3):
    """Append count smoke events and make sure the group exists."""
    for number in range(count):
        stream.xadd(event=make_smoke_event(number=number))
    stream.ensure_group()


def make_unit_stream() -> EventStream:
    """EventStream of the unit tests: never connects, the tests
    replace its _client by a mock."""
    return EventStream(
        url=UNIT_STREAM_URL,
        key=UNIT_STREAM_KEY,
        group='otlp',
        maxlen=10,
    )


def event_names_of(events_class: type) -> tuple:
    """The type names a class of events declares: its public
    constants."""
    return tuple(
        value for key, value in vars(events_class).items() if key.isupper()
    )


def event_name_values() -> Set[str]:
    """Every event type name of every events class."""
    return {
        name
        for events_class in EVENT_CLASSES
        for name in event_names_of(events_class=events_class)
    }
