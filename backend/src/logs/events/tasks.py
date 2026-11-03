import logging

from celery import shared_task
from django.conf import settings

from src.celery_app import periodic_lock
from src.logs.events.consumer import (
    LOCK_EXPIRE,
    MAX_ATTEMPTS,
    RETRY_BACKOFF,
    EventsConsumer,
)
from src.logs.events.sink import (
    DEFAULT_TIMEOUT,
    MAX_RETRY_AFTER,
    get_sink,
)
from src.logs.events.stream import get_stream
from src.utils.logging import capture_sentry_message_throttled

logger = logging.getLogger('pneumatic.events.consumer')
LOCK_ID = 'consume_events'
# The lock has to outlast the worst batch still in flight when the
# tick stops reading: every attempt times out, every pause is the
# longest one.
MAX_SECONDS = max(
    LOCK_EXPIRE
    - MAX_ATTEMPTS * sum(DEFAULT_TIMEOUT)
    - len(RETRY_BACKOFF) * max(*RETRY_BACKOFF, MAX_RETRY_AFTER),
    0.0,
)


@shared_task(ignore_result=True)
def consume_events():
    """Deliver a bounded tick without acknowledging unconfirmed batches."""
    if not settings.LOGS_BACKEND:
        return
    # The lock uses Redis too; it belongs inside the outage handler.
    try:
        with periodic_lock(LOCK_ID, lock_expire=LOCK_EXPIRE) as acquired:
            if not acquired:
                return
            consumer = EventsConsumer(
                stream=get_stream(),
                sink=get_sink(),
                batch_size=settings.LOGS_CONSUMER_BATCH_SIZE,
                max_seconds=MAX_SECONDS,
            )
            stats = consumer.run_once()
    except Exception as exc:  # noqa: BLE001
        error = type(exc).__name__
        logger.warning('Events consumer tick failed: %s', error)
        capture_sentry_message_throttled(
            message='Events consumer tick failed',
            data={'error': error},
        )
        return
    if stats.failed:
        capture_sentry_message_throttled(
            message='Events consumer left a batch pending',
            data={
                'delivered': stats.delivered,
                'duration_ms': stats.duration_ms,
            },
        )
    if stats.vanished or stats.malformed:
        capture_sentry_message_throttled(
            message='Events consumer cleared undeliverable entries',
            data={'vanished': stats.vanished, 'malformed': stats.malformed},
        )
