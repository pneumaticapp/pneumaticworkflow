from src.logs.events.reporting import REPORT_INTERVAL, report_error
from src.utils.logging import SentryLogLevel


def test_report_error__first_call__sent_with_the_error_level(mocker):

    # arrange
    monotonic_mock = mocker.patch(
        'src.logs.events.reporting.monotonic',
        return_value=100.0,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )

    # act
    report_error('Something failed', {'error': 'boom'})

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Something failed',
        data={'error': 'boom'},
        level=SentryLogLevel.ERROR,
    )
    monotonic_mock.assert_called_once_with()


def test_report_error__given_level__honoured(mocker):

    # arrange
    monotonic_mock = mocker.patch(
        'src.logs.events.reporting.monotonic',
        return_value=100.0,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )

    # act
    report_error(
        'Something failed',
        {'error': 'boom'},
        level=SentryLogLevel.WARNING,
    )

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Something failed',
        data={'error': 'boom'},
        level=SentryLogLevel.WARNING,
    )
    monotonic_mock.assert_called_once_with()


def test_report_error__same_message_within_the_interval__sent_once(
    mocker,
):

    # arrange
    monotonic_mock = mocker.patch(
        'src.logs.events.reporting.monotonic',
        side_effect=[100.0, 100.0 + REPORT_INTERVAL - 1],
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )
    report_error('Something failed', {'error': 'first'})

    # act
    report_error('Something failed', {'error': 'second'})

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Something failed',
        data={'error': 'first'},
        level=SentryLogLevel.ERROR,
    )
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_report_error__interval_passed__sent_again(mocker):

    """ An outage that lasts gets a message a minute, with the level
        of every call rather than of the first one. """

    # arrange
    monotonic_mock = mocker.patch(
        'src.logs.events.reporting.monotonic',
        side_effect=[100.0, 100.0 + REPORT_INTERVAL],
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )
    report_error('Something failed', {'error': 'first'})

    # act
    report_error(
        'Something failed',
        {'error': 'second'},
        level=SentryLogLevel.WARNING,
    )

    # assert
    assert capture_sentry_message_mock.call_count == 2
    capture_sentry_message_mock.assert_has_calls([
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
    ])
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_report_error__different_messages__each_sent(mocker):

    """ The throttle is per message: the stream and the collector
        failing at once are two subjects. """

    # arrange
    monotonic_mock = mocker.patch(
        'src.logs.events.reporting.monotonic',
        return_value=100.0,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )
    report_error('Stream failed', {'error': 'stream'})

    # act
    report_error('Collector failed', {'error': 'collector'})

    # assert
    assert capture_sentry_message_mock.call_count == 2
    capture_sentry_message_mock.assert_has_calls([
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
    ])
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_report_error__same_message_different_keys__each_sent(mocker):

    """ The key tells apart occurrences that share a message but
        not a cause: an unknown event type per name. """

    # arrange
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )

    # act
    report_error('Unknown event type', {'event_type': 'a.b'}, key='a.b')
    report_error('Unknown event type', {'event_type': 'c.d'}, key='c.d')
    report_error('Unknown event type', {'event_type': 'a.b'}, key='a.b')

    # assert
    assert capture_sentry_message_mock.call_count == 2
    capture_sentry_message_mock.assert_has_calls([
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
    ])
