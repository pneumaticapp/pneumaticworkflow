import logging

from celery import shared_task
from django.conf import settings

from src.celery_app import periodic_lock
from src.logs.events.consumer import (
    LOCK_EXPIRE,
    ConsumerStats,
    EventsConsumer,
    tick_budget,
)
from src.logs.events.emitter import logs_enabled
from src.logs.events.reporting import report_error
from src.logs.events.sinks.otlp import (
    DEFAULT_TIMEOUT,
    MAX_RETRY_AFTER,
    get_sink,
)
from src.logs.events.stream import get_stream

logger = logging.getLogger('pneumatic.events.consumer')

LOCK_ID = 'consume_events'
MAX_SECONDS = tick_budget(
    send_seconds=sum(DEFAULT_TIMEOUT),
    max_retry_after=MAX_RETRY_AFTER,
)


@shared_task(ignore_result=True)
def consume_events() -> None:

    """ Beat task: deliver one portion of the stream to the
        collector. Ticks never overlap thanks to the lock, and the
        tick budget (MAX_SECONDS) keeps a tick shorter than the lock
        even with the slowest batch in flight.

        Nothing raises out of here, the lock included: a beat task
        that fails every 5 seconds is a Sentry flood, so every error
        is logged on each tick and reported once a minute. """

    if not logs_enabled():
        return
    # The lock lives in the cache, and the cache is the same Redis as
    # the buffer: the outage the tick is built to survive breaks the
    # lock first, so the lock has to be inside the try as well.
    try:
        with periodic_lock(LOCK_ID, lock_expire=LOCK_EXPIRE) as acquired:
            if not acquired:
                return
            stats = _run_tick()
    except Exception as exc:  # noqa: BLE001
        _report_tick_error('Events consumer tick failed', exc)
        return
    if stats.failed:
        _report_failed_delivery(stats)
    if stats.vanished or stats.malformed:
        _report_cleared_entries(stats)


def _run_tick() -> ConsumerStats:
    consumer = EventsConsumer(
        stream=get_stream(),
        sink=get_sink(),
        batch_size=settings.LOGS_CONSUMER_BATCH_SIZE,
        max_seconds=MAX_SECONDS,
    )
    return consumer.run_once()


def _report_tick_error(message: str, exc: Exception) -> None:

    """ Only the class of the error leaves: the text of a Redis error
        may carry the connection URL, and the password with it. """

    error = type(exc).__name__
    logger.warning('%s: %s', message, error)
    report_error(
        message=message,
        data={'error': error},
    )


def _report_failed_delivery(stats: ConsumerStats) -> None:

    """ The consumer already logged the batch; Sentry gets one
        message a minute for as long as the receiver stays down. """

    report_error(
        message='Events consumer left a batch pending',
        data={
            'delivered': stats.delivered,
            'duration_ms': stats.duration_ms,
        },
    )


def _report_cleared_entries(stats: ConsumerStats) -> None:

    """ The stream already logged the entries it cleared. A vanished
        one was trimmed off the stream while it was pending, an event
        lost to LOGS_STREAM_MAXLEN; a malformed one sits in the dead
        letter. Either is worth a message, once a minute. """

    report_error(
        message='Events consumer cleared undeliverable entries',
        data={
            'vanished': stats.vanished,
            'malformed': stats.malformed,
        },
    )
