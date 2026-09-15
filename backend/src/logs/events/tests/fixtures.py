import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    EVENT_CLASSES,
    EventCategory,
    event_names_of,
)
from src.logs.events.exceptions import SinkTemporaryError
from src.logs.events.schema import Actor, Event, EventObject
from src.logs.events.sinks.base import BaseSink
from src.logs.events.stream import (
    AUTOCLAIM_START,
    DEAD_MAXLEN,
    DEAD_SUFFIX,
    EventStream,
    ParsedEntries,
)
from src.processes.enums import WorkflowEventType

Entries = List[Tuple[str, Event]]

EVENT_TS = datetime(2026, 9, 8, 10, 15, 30, 123456, tzinfo=timezone.utc)
SERVICE_NAME = 'pneumatic-backend'
SMOKE_ACCOUNT_ID = 7
UNIT_STREAM_URL = 'redis://localhost:6379/4'
UNIT_STREAM_KEY = 'pneumatic:events-unit'
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@dataclass
class PendingEntry:

    """ One record of the pending entries list of the group. """

    entry_id: str
    event: Event
    consumer: str
    delivered_at: float = field(default_factory=monotonic)

    def idle_ms(self, now: float) -> float:
        return (now - self.delivered_at) * 1000


class FakeEventStream:

    """ In memory EventStream for unit tests: same interface, same
        delivery semantics (a group with a per consumer pending list),
        no Redis. Time is monotonic, so idle is set by delivered_at. """

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

    @property
    def dead_key(self) -> str:
        return f'{self.key}{DEAD_SUFFIX}'

    def xadd(self, event: Event) -> str:
        self._sequence += 1
        entry_id = f'{self._sequence}-0'
        stored = Event.from_dict(event.to_dict())
        stored.id = entry_id
        self.events.append((entry_id, stored))
        self._trim()
        return entry_id

    def ensure_group(self) -> None:
        self.group_created = True

    def read_pending(self, consumer: str, count: int) -> ParsedEntries:
        now = monotonic()
        entries = []
        for entry in self._pending_of(consumer)[:count]:

            # Reading own pending list resets idle, as XREADGROUP does.
            entry.delivered_at = now
            entries.append((entry.entry_id, entry.event))
        return ParsedEntries(events=entries)

    def read_new(self, consumer: str, count: int) -> ParsedEntries:
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
        start_id: str = AUTOCLAIM_START,
    ) -> ParsedEntries:
        now = monotonic()
        claimed = []
        for entry in self._sorted_pending():
            if len(claimed) >= count:
                break
            if entry.idle_ms(now) < min_idle_ms:
                continue
            entry.consumer = consumer
            entry.delivered_at = now
            claimed.append((entry.entry_id, entry.event))
        return ParsedEntries(events=claimed)

    def ack(self, ids: Iterable[str]) -> int:
        acked = 0
        for entry_id in ids:
            if self.pending.pop(entry_id, None) is not None:
                acked += 1
        return acked

    def dead_letter(
        self,
        entries: List[Tuple[str, Any]],
        reason: str,
    ) -> int:
        for entry_id, event in entries:
            self.dead.append((entry_id, event, reason))
        del self.dead[:-DEAD_MAXLEN]
        return self.ack([entry_id for entry_id, _ in entries])

    def last_event(self) -> Optional[Event]:

        """ Test helper: the event of the last xadd. """

        return self.events[-1][1] if self.events else None

    def _trim(self) -> None:
        extra = len(self.events) - self.maxlen
        if extra > 0:
            del self.events[:extra]
            self._delivered = max(self._delivered - extra, 0)

    def _pending_of(self, consumer: str) -> List[PendingEntry]:
        return [
            entry for entry in self._sorted_pending()
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

    """ Filled event of the 5.1 sample. Override only the fields the
        test is about, so an assertion reads as the difference. """

    fields: Dict[str, Any] = {
        'type': 'workflow.run',
        'category': EventCategory.WORKFLOWS,
        'service': SERVICE_NAME,
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

    """ A contract record as the consumer reads it off the stream.

        One file per event type the file service writes: the tests of
        the other writer compare what they build with the same file,
        so a rename on either side breaks both. """

    path = os.path.join(FIXTURES_DIR, name)
    with open(path, encoding='utf-8') as fixture:
        return json.load(fixture)


def load_file_service_contract() -> Dict[str, Any]:

    """ The names the two writers have to agree on besides the shape
        of a record: the stream both write into and the actor types
        the file service may put into a record. """

    path = os.path.join(FIXTURES_DIR, 'file_service_contract.json')
    with open(path, encoding='utf-8') as fixture:
        return json.load(fixture)


def make_smoke_event(number: int = 0) -> Event:

    """ Smallest event the pipeline accepts. """

    return Event(
        type='system.smoke',
        category=EventCategory.OTHER,
        ts=EVENT_TS,
        account_id=SMOKE_ACCOUNT_ID,
        object=EventObject(type='account', id=SMOKE_ACCOUNT_ID),
        payload={'number': number},
    )


def fill_stream(stream, count: int = 3) -> None:

    """ Append count smoke events and make sure the group exists. """

    for number in range(count):
        stream.xadd(make_smoke_event(number))
    stream.ensure_group()


def make_unit_stream() -> EventStream:

    """ EventStream of the unit tests: never connects, the tests
        replace its _client by a mock. """

    return EventStream(
        url=UNIT_STREAM_URL,
        key=UNIT_STREAM_KEY,
        group='otlp',
        maxlen=10,
    )


def event_name_values() -> Set[str]:

    """ Every event type name of every events class. """

    return {
        name
        for events_class in EVENT_CLASSES
        for name in event_names_of(events_class)
    }


def expected_workflow_events() -> Tuple[Tuple[int, str, str], ...]:

    """ (WorkflowEventType, event type, category) of every workflow
        event. Transcribed from the table of 5.1 of the plan on
        purpose: reading the answer out of the registry would compare
        it with itself. """

    workflows = EventCategory.WORKFLOWS
    tasks = EventCategory.TASKS
    return (
        (WorkflowEventType.RUN, 'workflow.run', workflows),
        (WorkflowEventType.COMPLETE, 'workflow.complete', workflows),
        (WorkflowEventType.TASK_START, 'task.start', tasks),
        (WorkflowEventType.TASK_COMPLETE, 'task.complete', tasks),
        (WorkflowEventType.TASK_REVERT, 'task.revert', tasks),
        (WorkflowEventType.COMMENT, 'task.comment', tasks),
        (WorkflowEventType.ENDED, 'workflow.ended', workflows),
        (WorkflowEventType.DELAY, 'workflow.delay', workflows),
        (WorkflowEventType.REVERT, 'workflow.revert', workflows),
        (WorkflowEventType.TASK_SKIP, 'task.skip', tasks),
        (
            WorkflowEventType.ENDED_BY_CONDITION,
            'workflow.ended_by_condition',
            workflows,
        ),
        (WorkflowEventType.URGENT, 'workflow.urgent', workflows),
        (WorkflowEventType.NOT_URGENT, 'workflow.not_urgent', workflows),
        (
            WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
            'task.skip_no_performers',
            tasks,
        ),
        (
            WorkflowEventType.TASK_PERFORMER_CREATED,
            'task.performer_created',
            tasks,
        ),
        (
            WorkflowEventType.TASK_PERFORMER_DELETED,
            'task.performer_deleted',
            tasks,
        ),
        (WorkflowEventType.FORCE_RESUME, 'workflow.force_resume', workflows),
        (WorkflowEventType.FORCE_DELAY, 'workflow.force_delay', workflows),
        (
            WorkflowEventType.DUE_DATE_CHANGED,
            'task.due_date_changed',
            tasks,
        ),
        (
            WorkflowEventType.SUB_WORKFLOW_RUN,
            'workflow.sub_workflow_run',
            workflows,
        ),
        (
            WorkflowEventType.TASK_PERFORMER_GROUP_CREATED,
            'task.performer_group_created',
            tasks,
        ),
        (
            WorkflowEventType.TASK_PERFORMER_GROUP_DELETED,
            'task.performer_group_deleted',
            tasks,
        ),
        (WorkflowEventType.TASK_DELAY, 'task.delay', tasks),
        (WorkflowEventType.TASK_DELEGATION, 'task.delegation', tasks),
    )


class FakeSink(BaseSink):

    """ Concrete BaseSink for the tests of its template method.

        error is what _send raises; raises is what _handle_error
        answers it with, a temporary error of the same text unless
        given. classify=False makes _handle_error return instead of
        raising, which is the contract every sink has to keep. """

    def __init__(
        self,
        error: Optional[Exception] = None,
        classify: bool = True,
        raises: Optional[Exception] = None,
    ):
        self.error = error
        self.classify = classify
        self.raises = raises
        self.handled: List[Exception] = []

    def _send(self, records: Entries) -> None:
        if self.error is not None:
            raise self.error

    def _handle_error(self, exc: Exception, records: Entries) -> None:
        self.handled.append(exc)
        if self.raises is not None:
            raise self.raises
        if self.classify:
            raise SinkTemporaryError(str(exc))
