import pytest

from src.utils import logging as sentry_logging
from src.utils.logging import (
    SENTRY_THROTTLE_SECONDS,
    SentryLogLevel,
    capture_sentry_message_throttled,
)


@pytest.fixture(autouse=True)
def reset_sentry_throttle():
    sentry_logging._sentry_last_messages.clear()


def test_capture_sentry_message_throttled__first_call__error_level(mocker):

    # arrange
    monotonic_mock = mocker.patch(
        'src.utils.logging.monotonic',
        return_value=100.0,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.utils.logging.capture_sentry_message',
    )

    # act
    capture_sentry_message_throttled(
        message='Something failed',
        data={'error': 'boom'},
    )

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Something failed',
        data={'error': 'boom'},
        level=SentryLogLevel.ERROR,
    )
    monotonic_mock.assert_called_once_with()


def test_capture_sentry_message_throttled__given_level__honoured(mocker):

    # arrange
    monotonic_mock = mocker.patch(
        'src.utils.logging.monotonic',
        return_value=100.0,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.utils.logging.capture_sentry_message',
    )

    # act
    capture_sentry_message_throttled(
        message='Something failed',
        data={'error': 'boom'},
        level=SentryLogLevel.WARNING,
    )

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Something failed',
        data={'error': 'boom'},
        level=SentryLogLevel.WARNING,
    )
    monotonic_mock.assert_called_once_with()


def test_capture_sentry_message_throttled__within_interval__sent_once(
    mocker,
):

    # arrange
    monotonic_mock = mocker.patch(
        'src.utils.logging.monotonic',
        side_effect=[100.0, 100.0 + SENTRY_THROTTLE_SECONDS - 1],
    )
    capture_sentry_message_mock = mocker.patch(
        'src.utils.logging.capture_sentry_message',
    )
    capture_sentry_message_throttled(
        message='Something failed',
        data={'error': 'first'},
    )

    # act
    capture_sentry_message_throttled(
        message='Something failed',
        data={'error': 'second'},
    )

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Something failed',
        data={'error': 'first'},
        level=SentryLogLevel.ERROR,
    )
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_capture_sentry_message_throttled__interval_passed__sent_again(mocker):
    """An outage that lasts gets a message a minute, with the level
    of every call rather than of the first one."""

    # arrange
    monotonic_mock = mocker.patch(
        'src.utils.logging.monotonic',
        side_effect=[100.0, 100.0 + SENTRY_THROTTLE_SECONDS],
    )
    capture_sentry_message_mock = mocker.patch(
        'src.utils.logging.capture_sentry_message',
    )
    capture_sentry_message_throttled(
        message='Something failed',
        data={'error': 'first'},
    )

    # act
    capture_sentry_message_throttled(
        message='Something failed',
        data={'error': 'second'},
        level=SentryLogLevel.WARNING,
    )

    # assert
    assert capture_sentry_message_mock.call_count == 2
    capture_sentry_message_mock.assert_has_calls(
        [
            mocker.call(
                message='Something failed',
                data={'error': 'first'},
                level=SentryLogLevel.ERROR,
            ),
            mocker.call(
                message='Something failed',
                data={'error': 'second'},
                level=SentryLogLevel.WARNING,
            ),
        ],
    )
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_capture_sentry_message_throttled__different_messages__each_sent(
    mocker,
):
    """The throttle is per message: the stream and the collector
    failing at once are two subjects."""

    # arrange
    monotonic_mock = mocker.patch(
        'src.utils.logging.monotonic',
        return_value=100.0,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.utils.logging.capture_sentry_message',
    )
    capture_sentry_message_throttled(
        message='Stream failed',
        data={'error': 'stream'},
    )

    # act
    capture_sentry_message_throttled(
        message='Collector failed',
        data={'error': 'collector'},
    )

    # assert
    assert capture_sentry_message_mock.call_count == 2
    capture_sentry_message_mock.assert_has_calls(
        [
            mocker.call(
                message='Stream failed',
                data={'error': 'stream'},
                level=SentryLogLevel.ERROR,
            ),
            mocker.call(
                message='Collector failed',
                data={'error': 'collector'},
                level=SentryLogLevel.ERROR,
            ),
        ],
    )
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_capture_sentry_message_throttled__different_keys__each_sent(mocker):
    """The key tells apart occurrences that share a message but
    not a cause: an unknown event type per name."""

    # arrange
    capture_sentry_message_mock = mocker.patch(
        'src.utils.logging.capture_sentry_message',
    )

    # act
    capture_sentry_message_throttled(
        message='Unknown event type',
        data={'event_type': 'a.b'},
        key='a.b',
    )
    capture_sentry_message_throttled(
        message='Unknown event type',
        data={'event_type': 'c.d'},
        key='c.d',
    )
    capture_sentry_message_throttled(
        message='Unknown event type',
        data={'event_type': 'a.b'},
        key='a.b',
    )

    # assert
    assert capture_sentry_message_mock.call_count == 2
    capture_sentry_message_mock.assert_has_calls(
        [
            mocker.call(
                message='Unknown event type',
                data={'event_type': 'a.b'},
                level=SentryLogLevel.ERROR,
            ),
            mocker.call(
                message='Unknown event type',
                data={'event_type': 'c.d'},
                level=SentryLogLevel.ERROR,
            ),
        ],
    )
