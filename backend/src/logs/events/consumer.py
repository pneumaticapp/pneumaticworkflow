import logging
import time
from dataclasses import dataclass
from functools import partial
from typing import Callable, Optional

from src.logs.enums import (
    DEFAULT_CONSUMER_BATCH_SIZE,
    DEFAULT_CONSUMER_IDLE_MS,
)
from src.logs.events.exceptions import (
    SinkPermanentError,
    SinkTemporaryError,
)
from src.logs.events.sinks.base import BaseSink
from src.logs.events.stream import Entries, EventStream, consumer_name

logger = logging.getLogger('pneumatic.events.consumer')

DEFAULT_MAX_BATCHES = 20
LOCK_EXPIRE = 120
RETRY_BACKOFF = (0.5, 1.0)
MAX_ATTEMPTS = len(RETRY_BACKOFF) + 1
DEFAULT_MAX_SECONDS = LOCK_EXPIRE / 2
REJECTED_REASON = 'rejected'


def tick_budget(
    send_seconds: float,
    max_retry_after: float,
    lock_expire: float = LOCK_EXPIRE,
) -> float:

    """ Seconds a tick may keep reading batches so that the batch in
        flight when the deadline is reached still ends before the lock
        expires. The worst batch is MAX_ATTEMPTS sends of send_seconds
        each, with a pause between them that a Retry-After of the
        receiver may stretch to max_retry_after. """

    pauses = len(RETRY_BACKOFF) * max(*RETRY_BACKOFF, max_retry_after)
    worst_batch = MAX_ATTEMPTS * send_seconds + pauses
    return max(lock_expire - worst_batch, 0.0)


@dataclass
class ConsumerStats:

    """ Result of a single tick, also the source of the log line.
        failed is read by the beat task: a batch left pending after
        every attempt is a delivery outage worth a Sentry message. """

    delivered: int = 0
    acked: int = 0
    dead: int = 0
    claimed: int = 0
    failed: bool = False
    duration_ms: int = 0


@dataclass
class TickBudget:

    """ One budget for the whole tick, shared by its three phases: the
        limit counts batches of any phase, and the deadline ends a
        tick that is slow rather than long. """

    batches: int
    deadline: float
    stopped: bool = False

    def spent(self) -> bool:
        return (
            self.stopped
            or self.batches <= 0
            or time.monotonic() >= self.deadline
        )

    def take(self) -> None:
        self.batches -= 1

    def stop(self) -> None:

        """ Nothing more goes out in this tick: the sink either keeps
            the batch pending or rejects it for good. """

        self.stopped = True


class EventsConsumer:

    """ One tick of the delivery loop: read the stream, hand the
        batches to the sink, ack what the sink accepted.

        Nothing is acked before the sink confirms delivery, so a
        crash costs a repeated record and never a lost one. """

    def __init__(
        self,
        stream: EventStream,
        sink: BaseSink,
        batch_size: int = DEFAULT_CONSUMER_BATCH_SIZE,
        max_batches: int = DEFAULT_MAX_BATCHES,
        idle_ms: int = DEFAULT_CONSUMER_IDLE_MS,
        consumer: Optional[str] = None,
        sleep: Callable[[float], None] = time.sleep,
        max_seconds: float = DEFAULT_MAX_SECONDS,
    ):
        self.stream = stream
        self.sink = sink
        self.batch_size = batch_size
        self.max_batches = max_batches
        self.max_seconds = max_seconds
        self.idle_ms = idle_ms
        self.consumer = consumer or consumer_name()
        # Injected so that tests spend no time in backoff.
        self.sleep = sleep

    def _autoclaim(self, stats: ConsumerStats) -> Entries:

        """ Entries of dead consumers, counted as claimed on the way:
            the one source whose entries the stats tell apart. """

        entries = self.stream.autoclaim(
            consumer=self.consumer,
            min_idle_ms=self.idle_ms,
            count=self.batch_size,
        )
        stats.claimed += len(entries)
        return entries

    def _drain(
        self,
        read: Callable[[], Entries],
        stats: ConsumerStats,
        budget: TickBudget,
    ) -> None:

        """ Deliver batch after batch until the source runs dry or the
            tick budget is spent. """

        while not budget.spent():
            entries = read()
            if not entries:
                return
            budget.take()
            self._deliver(entries, stats, budget)

    def _deliver(
        self,
        entries: Entries,
        stats: ConsumerStats,
        budget: TickBudget,
    ) -> None:

        """ Send one batch, retrying only what is worth retrying. """

        for attempt in range(MAX_ATTEMPTS):
            try:
                self.sink.send(entries)
            except SinkPermanentError as exc:
                self._dead_letter(entries, stats, exc)
                budget.stop()
                return
            except SinkTemporaryError as exc:
                if attempt == MAX_ATTEMPTS - 1:
                    self._give_up(entries, stats, exc)
                    budget.stop()
                    return
                self.sleep(self._delay(attempt, exc))
                continue
            self._ack(entries, stats)
            return

    def _ack(self, entries: Entries, stats: ConsumerStats) -> None:
        stats.delivered += len(entries)
        stats.acked += self.stream.ack(
            [entry_id for entry_id, _ in entries],
        )

    def _dead_letter(
        self,
        entries: Entries,
        stats: ConsumerStats,
        exc: SinkPermanentError,
    ) -> None:

        """ The batch will never be accepted: park it aside and ack,
            a poison record must not block the stream. The tick ends
            here: the reason is usually the receiver, not the batch,
            and carrying the next batches into the dead letter at full
            speed would lose them all. """

        logger.error(
            'Dead lettering %s records: %s', len(entries), exc,
        )
        stats.dead += len(entries)
        stats.acked += self.stream.dead_letter(
            entries, reason=REJECTED_REASON,
        )

    def _give_up(
        self,
        entries: Entries,
        stats: ConsumerStats,
        exc: SinkTemporaryError,
    ) -> None:
        stats.failed = True
        logger.warning(
            '%s records left pending after %s attempts: %s',
            len(entries),
            MAX_ATTEMPTS,
            exc,
        )

    @staticmethod
    def _delay(attempt: int, exc: SinkTemporaryError) -> float:

        """ The sink may know better: a short Retry-After of the
            receiver wins over the fixed backoff. """

        return exc.retry_after or RETRY_BACKOFF[attempt]

    def run_once(self) -> ConsumerStats:

        """ Read own pending entries first (they would otherwise wait
            for the idle timeout), then take over the entries of dead
            consumers, then read new ones. All three phases spend one
            budget, so the tick is bounded no matter which of them
            finds the entries.

            A batch that cannot be delivered ends the tick: its
            entries stay pending and go out with the next one. """

        started = time.monotonic()
        stats = ConsumerStats()
        budget = TickBudget(
            batches=self.max_batches,
            deadline=started + self.max_seconds,
        )
        self.stream.ensure_group()
        self._drain(
            read=partial(
                self.stream.read_pending,
                consumer=self.consumer,
                count=self.batch_size,
            ),
            stats=stats,
            budget=budget,
        )
        self._drain(
            read=partial(self._autoclaim, stats),
            stats=stats,
            budget=budget,
        )
        self._drain(
            read=partial(
                self.stream.read_new,
                consumer=self.consumer,
                count=self.batch_size,
            ),
            stats=stats,
            budget=budget,
        )
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
