import logging

import redis

from src.logs.enums import LogsBackend
from src.logs.events.consumer import (
    LOCK_EXPIRE,
    ConsumerStats,
)
from src.logs.events.tasks import (
    LOCK_ID,
    MAX_SECONDS,
    consume_events,
)


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
    events_enabled.LOGS_CONSUMER_BATCH_SIZE = 500
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream_mock = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream_mock,
    )
    sink_mock = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink_mock,
    )
    consumer_mock = mocker.Mock()
    consumer_mock.run_once.return_value = ConsumerStats(delivered=3, acked=3)
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer_mock,
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
        stream=stream_mock,
        sink=sink_mock,
        batch_size=500,
        max_seconds=MAX_SECONDS,
    )
    consumer_mock.run_once.assert_called_once_with()
    report_error_mock.assert_not_called()


def test_consume_events__redis_error__only_error_class_reported(
    mocker,
    events_enabled,
    caplog,
):

    """ A Redis outage is logged every tick and reported once a
        minute, without a traceback flood in the Celery log. The text
        of the error may hold the connection URL with the password:
        neither the log nor Sentry gets it. """

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events.consumer')
    events_enabled.LOGS_CONSUMER_BATCH_SIZE = 500
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream_mock = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream_mock,
    )
    sink_mock = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink_mock,
    )
    error = redis.ConnectionError(
        'Error connecting to redis://:secret@redis:6379/4',
    )
    consumer_mock = mocker.Mock()
    consumer_mock.run_once.side_effect = error
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer_mock,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    assert caplog.messages == ['Events consumer tick failed: ConnectionError']
    report_error_mock.assert_called_once_with(
        message='Events consumer tick failed',
        data={'error': 'ConnectionError'},
    )
    consumer_mock.run_once.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream_mock,
        sink=sink_mock,
        batch_size=500,
        max_seconds=MAX_SECONDS,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
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
        data={'error': 'OSError'},
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
    events_enabled.LOGS_CONSUMER_BATCH_SIZE = 500
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream_mock = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream_mock,
    )
    sink_mock = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink_mock,
    )
    consumer_mock = mocker.Mock()
    consumer_mock.run_once.return_value = ConsumerStats(
        delivered=1000,
        acked=1000,
        failed=True,
        duration_ms=4500,
    )
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer_mock,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    report_error_mock.assert_called_once_with(
        message='Events consumer left a batch pending',
        data={
            'delivered': 1000,
            'duration_ms': 4500,
        },
    )
    consumer_mock.run_once.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream_mock,
        sink=sink_mock,
        batch_size=500,
        max_seconds=MAX_SECONDS,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )


def test_consume_events__vanished_entries__reported(
    mocker,
    events_enabled,
):

    """ A record trimmed off the stream while it was pending is an
        event lost to LOGS_STREAM_MAXLEN: worth a message. """

    # arrange
    events_enabled.LOGS_CONSUMER_BATCH_SIZE = 500
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream_mock = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream_mock,
    )
    sink_mock = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink_mock,
    )
    consumer_mock = mocker.Mock()
    consumer_mock.run_once.return_value = ConsumerStats(vanished=2)
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer_mock,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    report_error_mock.assert_called_once_with(
        message='Events consumer cleared undeliverable entries',
        data={
            'vanished': 2,
            'malformed': 0,
        },
    )
    consumer_mock.run_once.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream_mock,
        sink=sink_mock,
        batch_size=500,
        max_seconds=MAX_SECONDS,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )


def test_consume_events__malformed_entries__reported(
    mocker,
    events_enabled,
):

    # arrange
    events_enabled.LOGS_CONSUMER_BATCH_SIZE = 500
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.return_value = True
    stream_mock = mocker.Mock()
    get_stream_mock = mocker.patch(
        'src.logs.events.tasks.get_stream',
        return_value=stream_mock,
    )
    sink_mock = mocker.Mock()
    get_sink_mock = mocker.patch(
        'src.logs.events.tasks.get_sink',
        return_value=sink_mock,
    )
    consumer_mock = mocker.Mock()
    consumer_mock.run_once.return_value = ConsumerStats(
        delivered=3,
        acked=4,
        malformed=1,
    )
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
        return_value=consumer_mock,
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    report_error_mock.assert_called_once_with(
        message='Events consumer cleared undeliverable entries',
        data={
            'vanished': 0,
            'malformed': 1,
        },
    )
    consumer_mock.run_once.assert_called_once_with()
    consumer_class_mock.assert_called_once_with(
        stream=stream_mock,
        sink=sink_mock,
        batch_size=500,
        max_seconds=MAX_SECONDS,
    )
    get_stream_mock.assert_called_once_with()
    get_sink_mock.assert_called_once_with()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )


def test_consume_events__lock_unavailable__reported_not_raised(
    mocker,
    events_enabled,
    caplog,
):

    """ The lock lives in the same Redis as the buffer: when the
        buffer is down the lock is down first, and that must not
        raise out of the beat task either. """

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events.consumer')
    error = redis.ConnectionError('connection refused')
    periodic_lock_mock = mocker.patch(
        'src.logs.events.tasks.periodic_lock',
    )
    periodic_lock_mock.return_value.__enter__.side_effect = error
    consumer_class_mock = mocker.patch(
        'src.logs.events.tasks.EventsConsumer',
    )
    report_error_mock = mocker.patch('src.logs.events.tasks.report_error')

    # act
    consume_events()

    # assert
    assert caplog.messages == ['Events consumer tick failed: ConnectionError']
    report_error_mock.assert_called_once_with(
        message='Events consumer tick failed',
        data={'error': 'ConnectionError'},
    )
    consumer_class_mock.assert_not_called()
    periodic_lock_mock.assert_called_once_with(
        LOCK_ID, lock_expire=LOCK_EXPIRE,
    )
