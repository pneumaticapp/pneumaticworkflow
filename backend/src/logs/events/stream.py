import json
import logging
import socket
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import redis
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from src.logs.events.exceptions import EventsError
from src.logs.events.schema import Event

logger = logging.getLogger('pneumatic.events')

CONNECT_TIMEOUT = 1
SOCKET_TIMEOUT = 2
BUSYGROUP = 'BUSYGROUP'
DEAD_SUFFIX = ':dead'
DEAD_MAXLEN = 10000
NEW_ENTRIES = '>'
PENDING_ENTRIES = '0'
AUTOCLAIM_START = '0-0'
MALFORMED_REASON = 'malformed'

Entries = List[Tuple[str, Event]]
RawEntries = List[Tuple[str, dict]]


@dataclass
class ParsedEntries:

    """ What one answer of Redis holds.

        Three kinds of entries come back besides the good ones, all
        after the stream was trimmed past records that were still
        pending: XAUTOCLAIM of Redis 6.2 answers a deleted record as
        a (None, None) pair, XREADGROUP answers it as an id with no
        fields. Both are gone for good, nothing can be delivered or
        parked: the id, when there is one, is acked and the pair is
        dropped. A record that is there but cannot be parsed goes to
        the dead letter. """

    events: Entries = field(default_factory=list)
    malformed: RawEntries = field(default_factory=list)
    vanished: List[str] = field(default_factory=list)


def _parse_entries(entries: list) -> ParsedEntries:

    """ Sort the answer of Redis into the three kinds. Reading only:
        the caller acks and parks, so that what happens to an entry
        stays in one place. """

    parsed = ParsedEntries()
    for entry_id, fields in entries:
        if entry_id is None:
            continue
        if not fields:
            parsed.vanished.append(entry_id)
            continue
        event = _to_event(entry_id, fields)
        if event is None:
            parsed.malformed.append((entry_id, fields))
        else:
            parsed.events.append((entry_id, event))
    return parsed


def _to_event(entry_id: str, fields: dict) -> Optional[Event]:
    try:
        event = Event.from_dict(json.loads(fields['data']))
    except (KeyError, TypeError, ValueError):
        return None
    event.id = entry_id
    return event


class EventStream:

    """ Redis Stream client: one stream, one consumer group.

        The client is created on the first call, so importing the
        module (and building settings) never opens a connection. """

    def __init__(self, url: str, key: str, group: str, maxlen: int):
        self.url = url
        self.key = key
        self.group = group
        self.maxlen = maxlen
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=CONNECT_TIMEOUT,
                socket_timeout=SOCKET_TIMEOUT,
            )
        return self._client

    @property
    def dead_key(self) -> str:
        return f'{self.key}{DEAD_SUFFIX}'

    def _read(self, consumer: str, count: int, last_id: str) -> Entries:
        response = self.client.xreadgroup(
            groupname=self.group,
            consumername=consumer,
            streams={self.key: last_id},
            count=count,
        )
        entries = []
        for _key, records in response or ():
            entries.extend(records)
        return self._to_events(entries)

    def _to_events(self, entries: list) -> Entries:

        """ Turn what Redis handed out into events, and clear the
            entries that cannot become one. """

        parsed = _parse_entries(entries)
        if parsed.vanished:
            logger.warning(
                'Trimmed pending events acked: %s', parsed.vanished,
            )
            self.ack(parsed.vanished)
        if parsed.malformed:
            logger.warning(
                'Malformed events dropped: %s',
                [entry_id for entry_id, _ in parsed.malformed],
            )
            self.dead_letter(parsed.malformed, MALFORMED_REASON)
        return parsed.events

    @staticmethod
    def _dead_fields(entry_id: str, event: Any, reason: str) -> Dict[str, str]:
        if isinstance(event, Event):
            data = event.to_dict()
        elif isinstance(event, dict):
            data = event
        else:
            data = {}
        return {
            'type': data.get('type') or '',
            'reason': reason,
            'source_id': entry_id,
            'data': json.dumps(data, cls=DjangoJSONEncoder),
        }

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def xadd(self, event: Event) -> str:

        """ Append the event, trimming the stream to MAXLEN. """

        return self.client.xadd(
            name=self.key,
            fields={
                'type': event.type,
                'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder),
            },
            maxlen=self.maxlen,
            approximate=True,
        )

    def ensure_group(self) -> None:

        """ Create the group from the very first entry (id '0'), so
            events written before the first consumer tick are read. """

        try:
            self.client.xgroup_create(
                name=self.key,
                groupname=self.group,
                id='0',
                mkstream=True,
            )
        except redis.ResponseError as exc:
            if BUSYGROUP not in str(exc):
                raise

    def read_pending(self, consumer: str, count: int) -> Entries:

        """ Entries this consumer read but did not ack yet. """

        return self._read(consumer, count, PENDING_ENTRIES)

    def read_new(self, consumer: str, count: int) -> Entries:

        """ Entries never delivered to the group. """

        return self._read(consumer, count, NEW_ENTRIES)

    def autoclaim(
        self,
        consumer: str,
        min_idle_ms: int,
        count: int,
        start_id: str = AUTOCLAIM_START,
    ) -> Entries:

        """ Take over entries stuck in the pending list of a dead
            consumer. The next cursor is dropped on purpose: every
            tick starts over from the beginning of the pending list. """

        response = self.client.xautoclaim(
            name=self.key,
            groupname=self.group,
            consumername=consumer,
            min_idle_time=min_idle_ms,
            start_id=start_id,
            count=count,
        )
        # Redis 6.2 answers [next_id, entries], with a (None, None)
        # pair for every claimed record the stream no longer holds;
        # Redis 7.0 drops those and adds the list of deleted ids.
        entries = response[1] if len(response) > 1 else []
        return self._to_events(entries)

    def ack(self, ids: Iterable[str]) -> int:
        ids = list(ids)
        if not ids:
            return 0
        return self.client.xack(self.key, self.group, *ids)

    def dead_letter(
        self,
        entries: List[Tuple[str, Any]],
        reason: str,
    ) -> int:

        """ Move undeliverable entries aside and ack them: a poison
            record must not block the stream. An entry holds an Event
            or, when it could not be parsed, its raw fields. """

        ids = []
        for entry_id, event in entries:
            self.client.xadd(
                name=self.dead_key,
                fields=self._dead_fields(entry_id, event, reason),
                maxlen=DEAD_MAXLEN,
                approximate=True,
            )
            ids.append(entry_id)
        return self.ack(ids)


_streams: Dict[Tuple[str, str, str, int], EventStream] = {}


def get_stream() -> EventStream:

    """ Shared stream client of the process: the connection pool is
        reused between emits. A settings change gives a new client. """

    if not settings.LOGS_REDIS_URL:

        # A clear message instead of the ValueError redis-py raises for
        # an empty url: the pipeline is on by default, so a deployment
        # that forgot the variable must be told what exactly is wrong.
        raise EventsError(
            'LOGS_REDIS_URL is empty while LOGS_BACKEND is not "none": '
            'the event pipeline has nowhere to write',
        )

    params = (
        settings.LOGS_REDIS_URL,
        settings.LOGS_STREAM_KEY,
        settings.LOGS_CONSUMER_GROUP,
        settings.LOGS_STREAM_MAXLEN,
    )
    stream = _streams.get(params)
    if stream is None:
        stream = EventStream(*params)
        _streams[params] = stream
    return stream


def consumer_name() -> str:

    """ One name per host, not per process. The ticks of the beat
        task never overlap (periodic_lock), so whichever worker
        process runs the next tick may take over the pending list of
        the previous one right away instead of waiting for it to go
        idle; and a deployment does not leave a trail of dead
        consumer names in the group. """

    return socket.gethostname()
