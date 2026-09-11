import logging

import pytest
import requests

from src.logs.events.exceptions import (
    SinkPermanentError,
    SinkTemporaryError,
)
from src.logs.events.sinks.otlp import (
    BODY_LIMIT,
    DEFAULT_TIMEOUT,
    JSON_HEADERS,
    OTLPSink,
    get_sink,
    without_userinfo,
)
from src.logs.events.tests.fakes import (
    OBSERVED_NS,
    assert_posted,
    build_sink_body,
    make_event,
)
from src.utils.logging import SentryLogLevel


def test_init__endpoint_with_a_slash__single_logs_path():

    # act
    sink = OTLPSink(endpoint='http://otel-collector:4318/')

    # assert
    assert sink.url == 'http://otel-collector:4318/v1/logs'
    assert sink.timeout == DEFAULT_TIMEOUT


def test_get_sink__settings__sink_of_the_endpoint(settings):

    # arrange
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'

    # act
    sink = get_sink()

    # assert
    assert sink.url == 'http://otel-collector:4318/v1/logs'


def test_get_sink__called_twice__same_sink(settings):

    """ One session per process: a session rebuilt every tick would
        open a new connection for every batch it sends. """

    # arrange
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'
    first = get_sink()

    # act
    second = get_sink()

    # assert
    assert second is first


def test_get_sink__changed_endpoint__new_sink(settings):

    # arrange
    settings.LOGS_OTLP_ENDPOINT = 'http://otel-collector:4318'
    first = get_sink()
    settings.LOGS_OTLP_ENDPOINT = 'http://collector.test:4318'

    # act
    second = get_sink()

    # assert
    assert second is not first
    assert second.url == 'http://collector.test:4318/v1/logs'


def test_send__ok_response__batch_posted_to_the_collector(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.return_value = {}
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    assert_posted(post_mock, records)
    response.raise_for_status.assert_called_once_with()
    response.json.assert_called_once_with()
    time_ns_mock.assert_called_once_with()
    report_error_mock.assert_not_called()


def test_send__no_records__nothing_posted(mocker):

    # arrange
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send([])

    # assert
    post_mock.assert_not_called()


def test_send__ok_response_without_a_body__delivered(mocker):

    """ The collector answers 200 with an empty body: reading it as
        JSON raises, and that must not fail the delivery. """

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.side_effect = ValueError('no json')
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    report_error_mock.assert_not_called()
    response.raise_for_status.assert_called_once_with()
    response.json.assert_called_once_with()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__ok_response_with_a_text_body__delivered(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.return_value = 'accepted'
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize(
    'partial_success',
    (
        {'rejectedLogRecords': 'many'},
        'nope',
        ['x'],
        None,
    ),
)
def test_send__unreadable_partial_success__delivered(
    mocker,
    partial_success,
):

    """ A partialSuccess that is not the documented object is not a
        reason to keep the batch: it was accepted. """

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.return_value = {'partialSuccess': partial_success}
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__partial_success__reported_but_delivered(mocker):

    """ Sending the dropped records again would change nothing, so
        the batch counts as delivered and gets acked. """

    # arrange
    records = [('1-0', make_event()), ('2-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.return_value = {
        'partialSuccess': {
            'rejectedLogRecords': '2',
            'errorMessage': 'too old',
        },
    }
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    report_error_mock.assert_called_once_with(
        message='OTLP endpoint dropped records of a batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'rejected': 2,
            'records': 2,
        },
        level=SentryLogLevel.WARNING,
    )
    assert_posted(post_mock, records)
    response.raise_for_status.assert_called_once_with()
    time_ns_mock.assert_called_once_with()


def test_send__full_success__nothing_reported(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.return_value = {'partialSuccess': {}}
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    response.raise_for_status.assert_called_once_with()
    time_ns_mock.assert_called_once_with()


def test_send__server_error__temporary_error(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=503, headers={}, content=b'overloaded')
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == 'http://otel-collector:4318/v1/logs answered 503'
    assert ex.value.retry_after is None
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize('status', (401, 403, 404, 405))
def test_send__misconfigured_endpoint__temporary_error(mocker, status):

    """ 401, 403, 404 and 405 come from the endpoint or the proxy in
        front of it, not from the batch: the records wait in the
        stream instead of going to the dead letter. """

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(
        status_code=status,
        headers={},
        content=b'no route',
    )
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        f'http://otel-collector:4318/v1/logs answered {status}'
    )
    assert ex.value.retry_after is None
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
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
    header,
    retry_after,
):

    """ Only a short pause is honoured: a longer one belongs to the
        next tick, a zero, a negative one and the HTTP date form are
        ignored. """

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(
        status_code=429,
        headers={'Retry-After': header},
        content=b'slow down',
    )
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == 'http://otel-collector:4318/v1/logs answered 429'
    assert ex.value.retry_after == retry_after
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize('headers', ({}, None))
def test_send__too_many_requests_without_the_header__no_delay(
    mocker,
    headers,
):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(
        status_code=429,
        headers=headers,
        content=b'slow down',
    )
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert ex.value.retry_after is None
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__bad_request__permanent_error_with_the_body(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=400, headers={}, content=b'x' * 600)
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'http://otel-collector:4318/v1/logs answered 400 for 1 records: '
        f'{"x" * BODY_LIMIT}'
    )
    report_error_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'status': 400,
            'records': 1,
            'body': 'x' * BODY_LIMIT,
        },
    )
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


@pytest.mark.parametrize('status', (413, 415, 422))
def test_send__batch_condemned_by_the_status__permanent_error(
    mocker,
    status,
):

    """ A body too large, a wrong content type and an unprocessable
        record are about this very batch: sending it again would
        block the stream on it forever. """

    # arrange
    records = [('1-0', make_event()), ('2-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(
        status_code=status,
        headers={},
        content=b'rejected',
    )
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        f'http://otel-collector:4318/v1/logs answered {status} '
        'for 2 records: rejected'
    )
    report_error_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'status': status,
            'records': 2,
            'body': 'rejected',
        },
    )
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__unreadable_error_body__permanent_error_without_it(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=413, headers={}, content=None)
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'http://otel-collector:4318/v1/logs answered 413 for 1 records: '
    )
    report_error_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'http://otel-collector:4318/v1/logs',
            'status': 413,
            'records': 1,
            'body': '',
        },
    )
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__connection_error__temporary_error(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    error = requests.ConnectionError('refused')
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        side_effect=error,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'http://otel-collector:4318/v1/logs: ConnectionError'
    )
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__read_timeout__temporary_error(mocker):

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    error = requests.Timeout('too slow')
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        side_effect=error,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'http://otel-collector:4318/v1/logs: Timeout'
    )
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__error_without_a_response__temporary_error(mocker):

    """ An unknown failure keeps the batch pending, never acked. """

    # arrange
    records = [('1-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    error = requests.TooManyRedirects('lost')
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        side_effect=error,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'http://otel-collector:4318/v1/logs: TooManyRedirects'
    )
    report_error_mock.assert_not_called()
    assert_posted(post_mock, records)
    time_ns_mock.assert_called_once_with()


def test_send__error_while_building_the_batch__permanent_error(
    mocker,
    settings,
):

    """ An error that is not about the transport comes from the
        records themselves: sending them again would block the stream
        on the same batch forever, so they go to the dead letter. """

    # arrange
    settings.LOGS_SERVICE_NAME = 'pneumatic-backend'
    settings.LOGS_SERVICE_VERSION = '1.0.0'
    settings.CONFIGURATION_CURRENT = 'Testing'
    records = [('1-0', make_event())]
    error = AttributeError('boom')
    build_otlp_payload_mock = mocker.patch(
        'src.logs.events.sinks.otlp.build_otlp_payload',
        side_effect=error,
    )
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        f'OTLP batch cannot be built (1 records): {error!r}'
    )
    report_error_mock.assert_called_once_with(
        message='OTLP batch cannot be built',
        data={'records': 1, 'error': repr(error)},
    )
    build_otlp_payload_mock.assert_called_once_with(
        records,
        service_name='pneumatic-backend',
        service_version='1.0.0',
        environment='Testing',
        observed_ns=OBSERVED_NS,
    )
    time_ns_mock.assert_called_once_with()
    post_mock.assert_not_called()


def test_send__payload_that_is_a_list__delivered(mocker):

    """ A record written by hand into the stream is sent as it is,
        with the payload under a single attribute. """

    # arrange
    records = [('1-0', make_event(payload=[1, 'two']))]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=200, headers={})
    response.json.return_value = {}
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='http://otel-collector:4318')

    # act
    sink.send(records)

    # assert
    assert_posted(post_mock, records)
    report_error_mock.assert_not_called()
    time_ns_mock.assert_called_once_with()


def test_send__own_session__reused_between_batches(mocker):

    # arrange
    first_records = [('1-0', make_event())]
    second_records = [('2-0', make_event())]
    time_ns_mock = mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    session_mock = mocker.Mock()
    # Named, so that the calls on the response are not recorded as
    # calls of the session (a nameless return value gets a parent).
    response = mocker.Mock(name='response', status_code=200, headers={})
    response.json.return_value = {}
    session_mock.post.return_value = response
    sink = OTLPSink(
        endpoint='http://otel-collector:4318',
        session=session_mock,
    )

    # act
    sink.send(first_records)
    sink.send(second_records)

    # assert
    assert session_mock.post.call_count == 2
    session_mock.post.assert_has_calls([
        mocker.call(
            'http://otel-collector:4318/v1/logs',
            data=build_sink_body(first_records, OBSERVED_NS),
            headers=JSON_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        ),
        mocker.call(
            'http://otel-collector:4318/v1/logs',
            data=build_sink_body(second_records, OBSERVED_NS),
            headers=JSON_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        ),
    ])
    assert time_ns_mock.call_count == 2
    time_ns_mock.assert_has_calls([mocker.call(), mocker.call()])


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        (
                'http://otel-collector:4318/v1/logs',
                'http://otel-collector:4318/v1/logs',
        ),
        (
                'https://user:secret@collector.test/v1/logs',
                'https://collector.test/v1/logs',
        ),
        (
                'https://user:secret@collector.test:4318/v1/logs',
                'https://collector.test:4318/v1/logs',
        ),
        (
                'https://token@collector.test/v1/logs',
                'https://collector.test/v1/logs',
        ),
    ],
)
def test_without_userinfo__url__credential_dropped(url, expected):

    # act
    result = without_userinfo(url)

    # assert
    assert result == expected


def test_send__endpoint_with_credential__not_in_the_error(mocker):

    """ The endpoint is the one place a receiver credential can be
        put, and the messages of the sink reach the log and Sentry:
        neither the temporary error nor the transport error may
        repeat it. """

    # arrange
    records = [('1-0', make_event())]
    mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=503, headers={}, content=b'')
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    post_mock = mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='https://user:secret@collector.test')

    # act
    with pytest.raises(SinkTemporaryError) as ex:
        sink.send(records)

    # assert
    assert sink.url == 'https://user:secret@collector.test/v1/logs'
    assert str(ex.value) == 'https://collector.test/v1/logs answered 503'
    assert 'secret' not in str(ex.value)
    report_error_mock.assert_not_called()
    post_mock.assert_called_once_with(
        'https://user:secret@collector.test/v1/logs',
        data=build_sink_body(records, OBSERVED_NS),
        headers=JSON_HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )


def test_send__rejected_with_credential_in_endpoint__report_without_it(
    mocker,
    caplog,
):

    # arrange
    caplog.set_level(logging.ERROR, logger='pneumatic.events')
    records = [('1-0', make_event())]
    mocker.patch(
        'src.logs.events.sinks.otlp.time.time_ns',
        return_value=OBSERVED_NS,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.sinks.otlp.report_error',
    )
    response = mocker.Mock(status_code=400, headers={}, content=b'bad')
    response.raise_for_status.side_effect = requests.HTTPError(
        response=response,
    )
    mocker.patch(
        'src.logs.events.sinks.otlp.requests.Session.post',
        return_value=response,
    )
    sink = OTLPSink(endpoint='https://user:secret@collector.test')

    # act
    with pytest.raises(SinkPermanentError) as ex:
        sink.send(records)

    # assert
    assert str(ex.value) == (
        'https://collector.test/v1/logs answered 400 for 1 records: bad'
    )
    assert caplog.messages == [
        'https://collector.test/v1/logs answered 400 for 1 records: bad',
    ]
    report_error_mock.assert_called_once_with(
        message='OTLP endpoint rejected the batch',
        data={
            'url': 'https://collector.test/v1/logs',
            'status': 400,
            'records': 1,
            'body': 'bad',
        },
    )


def test_body_prefix__bytes_not_utf8__replaced_not_raised(mocker):

    # arrange
    response = mocker.Mock(content=b'\xff\xfe bad')

    # act
    result = OTLPSink._body_prefix(response)

    # assert
    assert result == '\ufffd\ufffd bad'
