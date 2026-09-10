import logging

import redis

from src.logs.enums import LogsBackend
from src.logs.events.consumer import (
    LOCK_EXPIRE,
    MAX_ATTEMPTS,
    ConsumerStats,
    tick_budget,
)
from src.logs.events.exceptions import EventsError
from src.logs.events.sinks.otlp import DEFAULT_TIMEOUT, MAX_RETRY_AFTER
from src.logs.events.tasks import (
    LOCK_ID,
    MAX_SECONDS,
    consume_events,
)


def test_max_seconds__otlp_timeouts__budget_of_the_lock():

    """ The reading budget of a tick leaves room for the slowest
        batch the OTLP sink may still be sending. """

    # act
    expected = tick_budget(
        send_seconds=sum(DEFAULT_TIMEOUT),
        max_retry_after=MAX_RETRY_AFTER,
    )

    # assert
    assert expected == MAX_SECONDS
    assert 0 < MAX_SECONDS < LOCK_EXPIRE


def test_consume_events__pipeline_off__lock_not_taken(mocker, settings):

    # arrange
    settings.LOGS_BACKEND = LogsBackend.NONE
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    periodic_lock_mock.assert_not_called()
    consumer_class_mock.assert_not_called()
    report_error_mock.assert_not_called()


def test_consume_events__lock_taken__tick_skipped(mocker, events_enabled):

    # arrange
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = False
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
    )
    get_stream_mock = mocker.patch('src.logs.events.tasks.get_stream')
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )
    consumer_class_mock.assert_not_called()
    get_stream_mock.assert_not_called()
    report_error_mock.assert_not_called()


def test_consume_events__lock_acquired__consumer_runs_once(
    mocker,
    events_enabled,
):

    # arrange
    events_enabled.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'
    events_enabled.LOGS_CONSUMER_BATCH_SIZE = 500
    events_enabled.LOGS_CONSUMER_IDLE_MS = 30000
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream,
    )
    sink = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink,
    )
    consumer = mocker.Mock()
    consumer.run_once.return_value = ConsumerStats(delivered=3, acked=3)
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream,
        sink=sink,
        batch_size=500,
        idle_ms=30000,
        max_seconds=MAX_SECONDS,
    )
    consumer.run_once.assert_called_once_with()
    report_error_mock.assert_not_called()


def test_consume_events__redis_error__reported_to_sentry(
    mocker,
    events_enabled,
    caplog,
):

    """ A Redis outage is logged every tick and reported once a
        minute, without a traceback flood in the Celery log. """

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events.consumer')
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream,
    )
    sink = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink,
    )
    error = redis.ConnectionError('connection refused')
    consumer = mocker.Mock()
    consumer.run_once.side_effect = error
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    assert caplog.messages == [f'Events consumer tick failed: {error}']
    report_error_mock.assert_called_once_with(
        message='Events consumer tick failed',
        data={'error': repr(error)},
    )
    consumer.run_once.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream,
        sink=sink,
        batch_size=events_enabled.LOGS_CONSUMER_BATCH_SIZE,
        idle_ms=events_enabled.LOGS_CONSUMER_IDLE_MS,
        max_seconds=MAX_SECONDS,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )


def test_consume_events__missing_stream_url__reported_not_raised(
    mocker,
    events_enabled,
):

    """ get_stream raises EventsError for an empty LOGS_REDIS_URL: a
        beat task that fails every 5 seconds is a Sentry flood, so
        the error is reported through the throttle instead. """

    # arrange
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    error = EventsError('LOGS_REDIS_URL is empty')
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        side_effect=error,
    )
    get_sink_mock = mocker.patch('src.logs.events.tasks.get_sink')
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    report_error_mock.assert_called_once_with(
        message='Events consumer tick failed',
        data={'error': repr(error)},
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_not_called()
    consumer_class_mock.assert_not_called()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )


def test_consume_events__os_error__reported_not_raised(
    mocker,
    events_enabled,
):

    """ A DNS failure of the Redis host is an OSError, not a
        RedisError: it has to be caught all the same. """

    # arrange
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    error = OSError('name or service not known')
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        side_effect=error,
    )
    get_sink_mock = mocker.patch('src.logs.events.tasks.get_sink')
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    report_error_mock.assert_called_once_with(
        message='Events consumer tick failed',
        data={'error': repr(error)},
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_not_called()
    consumer_class_mock.assert_not_called()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )


def test_consume_events__batch_left_pending__delivery_failure_reported(
    mocker,
    events_enabled,
):

    """ The consumer already logged the batch; Sentry gets one
        message a minute for as long as the receiver stays down. """

    # arrange
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream,
    )
    sink = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink,
    )
    consumer = mocker.Mock()
    consumer.run_once.return_value = ConsumerStats(
        delivered=1000,
        acked=1000,
        failed=True,
        duration_ms=4500,
    )
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    report_error_mock.assert_called_once_with(
        message='Events consumer left a batch pending',
        data={
            'attempts': MAX_ATTEMPTS,
            'delivered': 1000,
            'duration_ms': 4500,
        },
    )
    consumer.run_once.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream,
        sink=sink,
        batch_size=events_enabled.LOGS_CONSUMER_BATCH_SIZE,
        idle_ms=events_enabled.LOGS_CONSUMER_IDLE_MS,
        max_seconds=MAX_SECONDS,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )
