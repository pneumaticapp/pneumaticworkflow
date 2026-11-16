import json
import logging
from typing import Dict, Iterable, List, Optional, Tuple, Union

import redis
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from src.logs.events.entities import Event, ParsedEntries

logger = logging.getLogger('pneumatic.events')
CONNECT_TIMEOUT = 1
SOCKET_TIMEOUT = 2
STREAM_KEY = 'pneumatic:events'
CONSUMER_GROUP = 'otlp'
BUSYGROUP = 'BUSYGROUP'
DEAD_SUFFIX = ':dead'
DEAD_MAXLEN = 10000
NEW_ENTRIES = '>'
PENDING_ENTRIES = '0'
AUTOCLAIM_START = '0-0'
MALFORMED_REASON = 'malformed'
EVENT_RELATIONS = ('actor', 'object')


class EventStream:
    """Redis Stream client: one stream, one consumer group.

    The client is created on the first call, so importing the
    module (and building settings) never opens a connection."""

    def __init__(self, url: str, key: str, group: str, maxlen: int):
        self.url = url
        self.key = key
        self.group = group
        self.maxlen = maxlen
        self._client: Optional[redis.Redis] = None
        self._claim_cursors: Dict[str, str] = {}

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

    def xadd(self, event: Event) -> str:
        """Append the event, trimming the stream to MAXLEN."""
        return self.client.xadd(
            name=self.key,
            fields={
                'type': event.type,
                'data': json.dumps(event.to_dict(), cls=DjangoJSONEncoder),
            },
            maxlen=self.maxlen,
            approximate=True,
        )

    def ensure_group(self):
        """Create the group from the very first entry (id '0'), so
        events written before the first consumer tick are read."""
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

    def read(self, consumer: str, count: int, start_id: str) -> ParsedEntries:
        """Entries of the group: PENDING_ENTRIES reads the ones this
        consumer read but did not ack yet, NEW_ENTRIES the ones never
        delivered to the group."""
        response = self.client.xreadgroup(
            groupname=self.group,
            consumername=consumer,
            streams={self.key: start_id},
            count=count,
        )
        entries = []
        for _key, records in response or ():
            entries.extend(records)
        return self._clear_entries(entries)

    def autoclaim(
        self,
        consumer: str,
        min_idle_ms: int,
        count: int,
        start_id: Optional[str] = None,
    ) -> ParsedEntries:
        """Take over entries stuck in the pending list of a dead
        consumer. Resume the scan across pages and bounded ticks;
        an empty page can still have eligible entries after it.

        A pending record the stream no longer holds has no id to
        ack: Redis 7.0 removes it from the pending list on its
        own, Redis 6.2 keeps it there, and the claim above resets
        its idle time, so it costs one slot of count once per
        idle window until the group is recreated."""
        if start_id is None:
            start_id = self._claim_cursors.get(consumer, AUTOCLAIM_START)
        response = self.client.xautoclaim(
            name=self.key,
            groupname=self.group,
            consumername=consumer,
            min_idle_time=min_idle_ms,
            start_id=start_id,
            count=count,
        )
        entries = response[1] if len(response) > 1 else []
        parsed = self._clear_entries(entries)
        parsed.next_cursor = response[0]
        self._claim_cursors[consumer] = parsed.next_cursor
        return parsed

    def ack(self, ids: Iterable[str]) -> int:
        ids = list(ids)
        if not ids:
            return 0
        return self.client.xack(self.key, self.group, *ids)

    def dead_letter(
        self,
        entries: List[Tuple[str, Union[Event, dict]]],
        reason: str,
    ) -> int:
        """Move undeliverable entries aside and ack them: a poison
        record must not block the stream. An entry holds an Event
        or, when it could not be parsed, its raw fields.

        One pipeline for the whole batch: a rejected batch is as
        long as a delivered one, and a round trip per record would
        hold the tick for longer than the lock lasts. The ack
        rides in the same transaction, so a failure parks either
        everything or nothing."""
        if not entries:
            return 0
        pipe = self.client.pipeline(transaction=True)
        for entry_id, event in entries:
            data = event.to_dict() if isinstance(event, Event) else event
            pipe.xadd(
                name=f'{self.key}{DEAD_SUFFIX}',
                fields={
                    'type': data.get('type') or '',
                    'reason': reason,
                    'source_id': entry_id,
                    'data': json.dumps(data, cls=DjangoJSONEncoder),
                },
                maxlen=DEAD_MAXLEN,
                approximate=True,
            )
        pipe.xack(self.key, self.group, *[entry_id for entry_id, _ in entries])
        return pipe.execute()[-1]

    def _clear_entries(self, entries: list) -> ParsedEntries:
        """Turn what Redis handed out into events, and clear the
        entries that cannot become one. All three kinds go back
        to the caller, which counts the cleared ones.

        The types of the fields the sink builds on are checked too: a
        record written by hand with a number for the type passes
        Event.from_dict and would then break the whole batch in the
        sink instead of going to the dead letter alone."""
        parsed = ParsedEntries()
        for entry_id, fields in entries:
            if entry_id is None:
                continue
            if not fields:
                parsed.vanished.append(entry_id)
                continue
            try:
                data = json.loads(fields['data'])
            except (KeyError, TypeError, ValueError):
                data = None
            event = None
            if isinstance(data, dict) and all(
                data.get(name) is None or isinstance(data[name], dict)
                for name in EVENT_RELATIONS
            ):
                try:
                    event = Event.from_dict(data)
                except (KeyError, TypeError, ValueError):
                    event = None
            if event is None or not (
                isinstance(event.type, str)
                and isinstance(event.category, str)
                and isinstance(event.service, str)
                and isinstance(event.account_id, int)
                and isinstance(event.payload, dict)
            ):
                parsed.malformed.append((entry_id, fields))
                continue
            event.id = entry_id
            parsed.events.append((entry_id, event))
        if parsed.vanished:
            logger.warning(
                'Trimmed pending events acked: %s',
                len(parsed.vanished),
            )
            self.ack(parsed.vanished)
        if parsed.malformed:
            logger.warning(
                'Malformed events dropped: %s',
                len(parsed.malformed),
            )
            self.dead_letter(
                entries=parsed.malformed,
                reason=MALFORMED_REASON,
            )
        return parsed


_streams: Dict[Tuple[str, str, str, int], EventStream] = {}


def get_stream() -> EventStream:
    """Shared stream client of the process: the connection pool is
    reused between emits. A settings change gives a new client."""
    params = (
        settings.LOGS_REDIS_URL,
        STREAM_KEY,
        CONSUMER_GROUP,
        settings.LOGS_STREAM_MAXLEN,
    )
    stream = _streams.get(params)
    if stream is None:
        stream = EventStream(
            url=params[0],
            key=params[1],
            group=params[2],
            maxlen=params[3],
        )
        _streams[params] = stream
    return stream
