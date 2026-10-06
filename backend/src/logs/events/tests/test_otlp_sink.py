import logging

import pytest
import requests

from src.logs.events.exceptions import SinkPermanentError, SinkTemporaryError
from src.logs.events.sink import OTLPSink, get_sink
from src.logs.events.tests.fixtures import make_event
from src.utils.logging import SentryLogLevel


def test_init__endpoint_with_a_slash__single_logs_path():

    # arrange
    endpoint = 'http://otel-collector:4318/'

    # act
    sink = OTLPSink(endpoint=endpoint)

    # assert
    assert sink.url == 'http://otel-collector:4318/v1/logs'
    assert sink.timeout == (3.05, 10.0)


def test_get_sink__settings__sink_of_the_endpoint(settings):

    # arrange
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'

    # act
    sink = get_sink()

    # assert
    assert sink.url == 'http://otel-collector:4318/v1/logs'


def test_get_sink__called_twice__same_sink(settings):
    """One session per process: a session rebuilt every tick would
    open a new connection for every batch it sends."""

    # arrange
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'

    # act
    first = get_sink()
    second = get_sink()

    # assert
    assert second is first


def test_get_sink__changed_endpoint__new_sink(settings):

    # arrange
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'

    # act
    first = get_sink()
    settings.LOGS_OTLP_ENDPOINT = 'http://collector.test:4318'
    second = get_sink()

    # assert
    assert second is not first
    assert second.url == 'http://collector.test:4318/v1/logs'


def test_send__ok_response__batch_posted_to_the_collector(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event()), ('2-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.return_value = {}
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    time_ns_mock.assert_called_once_with()
    capture_sentry_mock.assert_not_called()


def test_send__no_records__nothing_posted(mocker):

    # arrange
    records = []
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    build_otlp_payload_mock.assert_not_called()
    post_mock.assert_not_called()


def test_send__ok_response_without_a_body__delivered(mocker, settings):
    """The collector answers 200 with an empty body: reading it as
    JSON raises, and that must not fail the delivery."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.side_effect = ValueError('no json')
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    capture_sentry_mock.assert_not_called()
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    time_ns_mock.assert_called_once_with()


def test_send__ok_response_with_a_text_body__delivered(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.return_value = 'accepted'
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    capture_sentry_mock.assert_not_called()
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize(
    'partial_success',
    ({'rejectedLogRecords': 'many'}, 'nope', ['x'], None),
)
def test_send__unreadable_partial_success__delivered(
    mocker,
    settings,
    partial_success,
):
    """A partialSuccess that is not the documented object is not a
    reason to keep the batch: it was accepted."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.return_value = {'partialSuccess': partial_success}
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    capture_sentry_mock.assert_not_called()
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    time_ns_mock.assert_called_once_with()


def test_send__partial_success__reported_but_delivered(mocker, settings):
    """Sending the dropped records again would change nothing, so
    the batch counts as delivered and gets acked."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event()), ('2-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.return_value = {
        'partialSuccess': {
            'rejectedLogRecords': '2',
            'errorMessage': 'too old',
        },
    }
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    capture_sentry_mock.assert_called_once_with(
        message='OTLP endpoint dropped records of a batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'rejected': 2,
            'records': 2,
        },
        level=SentryLogLevel.WARNING,
    )
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    time_ns_mock.assert_called_once_with()


def test_send__full_success__nothing_reported(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.return_value = {'partialSuccess': {}}
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    time_ns_mock.assert_called_once_with()


def test_send__no_release__batch_without_a_version(mocker, settings):
    """The version is RELEASE of .env, and a deployment may leave it
    out: the sink hands None to build_otlp_payload as it is. That
    None leaves service.version out of the batch, the branch of
    test_build__record_of_another_service__no_version."""

    # arrange
    settings.LOGS_SERVICE_VERSION = None
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=200, headers={})
    response_mock.json.return_value = {}
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records=records)

    # assert
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version=None,
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_called_once_with()
    time_ns_mock.assert_called_once_with()
    capture_sentry_mock.assert_not_called()


def test_send__server_error__temporary_error(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(
        status_code=503,
        headers={},
        content=b'overloaded',
    )
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert str(ex.value) == 'http://otel-collector:4318/v1/logs answered 503'
    assert ex.value.retry_after is None
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize('status', (401, 403, 404, 405))
def test_send__misconfigured_endpoint__temporary_error(
    mocker,
    settings,
    status,
):
    """401, 403, 404 and 405 come from the endpoint or the proxy in
    front of it, not from the batch: the records wait in the
    stream instead of going to the dead letter."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(
        status_code=status,
        headers={},
        content=b'no route',
    )
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value)
        == f'http://otel-collector:4318/v1/logs answered {status}'
    )
    assert ex.value.retry_after is None
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize(
    ('header', 'retry_after'),
    (
        ('5', 5.0),
        ('0.5', 0.5),
        ('10', 10.0),
        ('11', None),
        ('30', None),
        ('0', None),
        ('-1', None),
        ('Wed, 21 Oct 2026 07:28:00 GMT', None),
    ),
)
def test_send__too_many_requests__delay_of_the_header(
    mocker,
    settings,
    header,
    retry_after,
):
    """Only a short pause is honoured: a longer one belongs to the
    next tick, a zero, a negative one and the HTTP date form are
    ignored."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(
        status_code=429,
        headers={'Retry-After': header},
        content=b'slow down',
    )
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert str(ex.value) == 'http://otel-collector:4318/v1/logs answered 429'
    assert ex.value.retry_after == retry_after
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize('headers', ({}, None))
def test_send__too_many_requests_without_the_header__no_delay(
    mocker,
    settings,
    headers,
):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(
        status_code=429,
        headers=headers,
        content=b'slow down',
    )
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert ex.value.retry_after is None
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


def test_send__bad_request__answer_body_in_the_log_only(
    mocker,
    settings,
    caplog,
):
    """The answer quotes the refused records, personal data included:
    neither Sentry nor the text of the error may carry it."""

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(
        status_code=400,
        headers={},
        content=b'x' * 600,
    )
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value)
        == 'http://otel-collector:4318/v1/logs answered 400 for 1 records'
    )
    assert caplog.messages == [
        'http://otel-collector:4318/v1/logs answered 400 for 1 records: '
        + 'x' * 500,
    ]
    capture_sentry_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'status': 400,
            'records': 1,
        },
    )
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize('status', (413, 415, 422))
def test_send__batch_condemned_by_the_status__permanent_error(
    mocker,
    settings,
    status,
):
    """A body too large, a wrong content type and an unprocessable
    record are about this very batch: sending it again would
    block the stream on it forever."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event()), ('2-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(
        status_code=status,
        headers={},
        content=b'rejected',
    )
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records=records)

    # assert
    assert str(ex.value) == (
        f'http://otel-collector:4318/v1/logs answered {status} for 2 records'
    )
    capture_sentry_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'status': status,
            'records': 2,
        },
    )
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


def test_send__unreadable_error_body__permanent_error_logged_without_it(
    mocker,
    settings,
    caplog,
):

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=413, headers={}, content=None)
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value)
        == 'http://otel-collector:4318/v1/logs answered 413 for 1 records'
    )
    assert caplog.messages == [
        'http://otel-collector:4318/v1/logs answered 413 for 1 records: ',
    ]
    capture_sentry_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'status': 413,
            'records': 1,
        },
    )
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


def test_send__connection_error__temporary_error(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        side_effect=requests.ConnectionError('refused'),
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value) == 'http://otel-collector:4318/v1/logs: ConnectionError'
    )
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    time_ns_mock.assert_called_once_with()


def test_send__read_timeout__temporary_error(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        side_effect=requests.Timeout('too slow'),
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert str(ex.value) == 'http://otel-collector:4318/v1/logs: Timeout'
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    time_ns_mock.assert_called_once_with()


def test_send__error_without_a_response__temporary_error(mocker, settings):
    """An unknown failure keeps the batch pending, never acked."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        side_effect=requests.TooManyRedirects('lost'),
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value) == 'http://otel-collector:4318/v1/logs: TooManyRedirects'
    )
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='http://otel-collector:4318/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    time_ns_mock.assert_called_once_with()


def test_send__error_while_building_the_batch__permanent_error(
    mocker,
    settings,
):
    """An error that is not about the transport comes from the
    records themselves: sending them again would block the stream
    on the same batch forever, so they go to the dead letter."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        side_effect=AttributeError('boom'),
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value)
        == "OTLP batch cannot be built (1 records): AttributeError('boom')"
    )
    capture_sentry_mock.assert_called_once_with(
        message='OTLP batch cannot be built',
        data={'records': 1, 'error': "AttributeError('boom')"},
    )
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    time_ns_mock.assert_called_once_with()
    post_mock.assert_not_called()


def test_send__own_session__reused_between_batches(mocker, settings):

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    first_records = [('1-0', make_event())]
    second_records = [('2-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        side_effect=[{'resourceLogs': 'first'}, {'resourceLogs': 'second'}],
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    session_mock = mocker.Mock()
    response_mock = mocker.Mock(name='response', status_code=200, headers={})
    response_mock.json.return_value = {}
    session_mock.post.return_value = response_mock
    sink = OTLPSink(
        endpoint='http://otel-collector:4318',
        session=session_mock,
    )

    # act
    sink.send(records=first_records)
    sink.send(records=second_records)

    # assert
    assert session_mock.post.call_count == 2
    session_mock.post.assert_has_calls(
        [
            mocker.call(
                url='http://otel-collector:4318/v1/logs',
                data=b'{"resourceLogs": "first"}',
                headers={'Content-Type': 'application/json'},
                timeout=(3.05, 10.0),
            ),
            mocker.call(
                url='http://otel-collector:4318/v1/logs',
                data=b'{"resourceLogs": "second"}',
                headers={'Content-Type': 'application/json'},
                timeout=(3.05, 10.0),
            ),
        ],
    )
    assert build_otlp_payload_mock.call_count == 2
    build_otlp_payload_mock.assert_has_calls(
        [
            mocker.call(
                records=first_records,
                service_name='pneumatic-backend',
                service_version='1.0.0',
                environment='Testing',
                observed_ns=1788862535000000000,
            ),
            mocker.call(
                records=second_records,
                service_name='pneumatic-backend',
                service_version='1.0.0',
                environment='Testing',
                observed_ns=1788862535000000000,
            ),
        ],
    )
    assert response_mock.raise_for_status.call_count == 2
    response_mock.raise_for_status.assert_has_calls(
        [mocker.call(), mocker.call()],
    )
    assert response_mock.json.call_count == 2
    response_mock.json.assert_has_calls([mocker.call(), mocker.call()])
    assert time_ns_mock.call_count == 2
    time_ns_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_send__endpoint_with_credential__not_in_the_error(mocker, settings):
    """The endpoint is the one place a receiver credential can be
    put, and the messages of the sink reach the log and Sentry:
    neither the temporary error nor the transport error may
    repeat it."""

    # arrange
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=503, headers={}, content=b'')
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='https://user:secret@collector.test')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records=records)

    # assert
    assert sink.url == 'https://user:secret@collector.test/v1/logs'
    assert str(ex.value) == 'https://collector.test/v1/logs answered 503'
    capture_sentry_mock.assert_not_called()
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='https://user:secret@collector.test/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


def test_send__rejected_with_credential_in_endpoint__report_without_it(
    mocker,
    settings,
    caplog,
):

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sink.build_otlp_payload',
        return_value={'resourceLogs': []},
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sink.time.time_ns',
        return_value=1788862535000000000,
    )
    capture_sentry_mock = mocker.patch(
        'src.logs.events.sink.capture_sentry_message_throttled',
    )
    response_mock = mocker.Mock(status_code=400, headers={}, content=b'bad')
    response_mock.raise_for_status.side_effect = requests.HTTPError(
        response=response_mock,
    )
    post_mock = mocker.patch(
        'src.logs.events.sink.requests.Session.post',
        return_value=response_mock,
    )
    sink = OTLPSink(endpoint='https://user:secret@collector.test')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records=records)

    # assert
    assert (
        str(ex.value)
        == 'https://collector.test/v1/logs answered 400 for 1 records'
    )
    assert caplog.messages == [
        'https://collector.test/v1/logs answered 400 for 1 records: bad',
    ]
    capture_sentry_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'https://collector.test/v1/logs',
            'status': 400,
            'records': 1,
        },
    )
    build_otlp_payload_mock.assert_called_once_with(
        records=records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=1788862535000000000,
    )
    post_mock.assert_called_once_with(
        url='https://user:secret@collector.test/v1/logs',
        data=b'{"resourceLogs": []}',
        headers={'Content-Type': 'application/json'},
        timeout=(3.05, 10.0),
    )
    response_mock.raise_for_status.assert_called_once_with()
    response_mock.json.assert_not_called()
    time_ns_mock.assert_called_once_with()


def test_init__endpoint_with_path__logs_path_appended():
    """A path prefix is preserved when forming the collector URL."""

    # arrange
    endpoint = 'https://user:secret@collector.test/otel/'

    # act
    sink = OTLPSink(endpoint=endpoint)

    # assert
    assert sink.url == 'https://user:secret@collector.test/otel/v1/logs'
    assert sink.display_url == 'https://collector.test/otel/v1/logs'
