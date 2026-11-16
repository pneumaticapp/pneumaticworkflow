import logging
import socket
import time
from functools import partial
from typing import Callable, Optional

from django.conf import settings

from src.logs.events.entities import ConsumerStats, Entries, TickBudget
from src.logs.events.exceptions import SinkPermanentError, SinkTemporaryError
from src.logs.events.sink import OTLPSink
from src.logs.events.stream import (
    AUTOCLAIM_START,
    NEW_ENTRIES,
    PENDING_ENTRIES,
    EventStream,
)

logger = logging.getLogger('pneumatic.events.consumer')
DEFAULT_MAX_BATCHES = 20
LOCK_EXPIRE = 120
RETRY_BACKOFF = (0.5, 1.0)
MAX_ATTEMPTS = len(RETRY_BACKOFF) + 1
DEFAULT_MAX_SECONDS = LOCK_EXPIRE / 2
REJECTED_REASON = 'rejected'


class EventsConsumer:
    """Read pending, abandoned and new batches in one bounded tick."""

    def __init__(
        self,
        stream: EventStream,
        sink: OTLPSink,
        batch_size: int,
        max_batches: int = DEFAULT_MAX_BATCHES,
        idle_ms: Optional[int] = None,
        consumer: Optional[str] = None,
        sleep: Callable[[float], None] = time.sleep,
        max_seconds: float = DEFAULT_MAX_SECONDS,
    ):
        self.stream = stream
        self.sink = sink
        self.batch_size = batch_size
        self.max_batches = max_batches
        self.max_seconds = max_seconds
        if idle_ms is None:
            idle_ms = settings.LOGS_DEFAULT_CONSUMER_IDLE_MS
        self.idle_ms = idle_ms
        self.consumer = consumer or socket.gethostname()
        self.sleep = sleep

    def _deliver(
        self,
        entries: Entries,
        stats: ConsumerStats,
        budget: TickBudget,
    ):
        """Ack only after confirmation, retrying temporary failures."""
        for attempt in range(MAX_ATTEMPTS):
            try:
                self.sink.send(entries)
            except SinkPermanentError as exc:
                logger.error(
                    'Dead lettering %s records: %s',
                    len(entries),
                    exc,
                )
                stats.dead += len(entries)
                stats.acked += self.stream.dead_letter(
                    entries=entries,
                    reason=REJECTED_REASON,
                )
                budget.stopped = True
                return
            except SinkTemporaryError as exc:
                if attempt == MAX_ATTEMPTS - 1:
                    stats.failed = True
                    logger.warning(
                        '%s records left pending after %s attempts: %s',
                        len(entries),
                        MAX_ATTEMPTS,
                        exc,
                    )
                    budget.stopped = True
                    return
                self.sleep(exc.retry_after or RETRY_BACKOFF[attempt])
                continue
            stats.delivered += len(entries)
            stats.acked += self.stream.ack(
                [entry_id for entry_id, _ in entries],
            )
            return

    def run_once(self) -> ConsumerStats:
        """Leave retryable failures pending; park rejected batches."""
        started = time.monotonic()
        stats = ConsumerStats()
        budget = TickBudget(
            batches=self.max_batches,
            deadline=started + self.max_seconds,
        )
        self.stream.ensure_group()
        sources = (
            (
                partial(
                    self.stream.read,
                    consumer=self.consumer,
                    count=self.batch_size,
                    start_id=PENDING_ENTRIES,
                ),
                False,
            ),
            (
                partial(
                    self.stream.autoclaim,
                    consumer=self.consumer,
                    min_idle_ms=self.idle_ms,
                    count=self.batch_size,
                ),
                True,
            ),
            (
                partial(
                    self.stream.read,
                    consumer=self.consumer,
                    count=self.batch_size,
                    start_id=NEW_ENTRIES,
                ),
                False,
            ),
        )
        for read, claimed in sources:
            while (
                not budget.stopped
                and budget.batches > 0
                and time.monotonic() < budget.deadline
            ):
                parsed = read()
                stats.vanished += len(parsed.vanished)
                stats.malformed += len(parsed.malformed)
                if claimed:
                    stats.claimed += len(parsed.events)
                if parsed.events or (
                    claimed and parsed.next_cursor != AUTOCLAIM_START
                ):
                    budget.batches -= 1
                if not parsed.events:
                    if claimed and parsed.next_cursor != AUTOCLAIM_START:
                        continue
                    break
                self._deliver(
                    entries=parsed.events,
                    stats=stats,
                    budget=budget,
                )
                if claimed and parsed.next_cursor == AUTOCLAIM_START:
                    break
        stats.duration_ms = int((time.monotonic() - started) * 1000)
        logger.info(
            'delivered=%s acked=%s dead=%s claimed=%s in %s ms',
            stats.delivered,
            stats.acked,
            stats.dead,
            stats.claimed,
            stats.duration_ms,
        )
        return stats
