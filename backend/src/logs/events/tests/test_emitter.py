import logging

import pytest
import redis
from django.utils import timezone

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.enums import LogsBackend
from src.logs.events import emitter as emitter_module
from src.logs.events import services as services_module
from src.logs.events.emitter import (
    CIRCUIT_OPEN_SECONDS,
    NO_ACCOUNT,
    _build_event,
    _report_stream_error,
    _write,
    emit,
)
from src.logs.events.enums import (
    ApiKeyEvents,
    EventCategory,
    UserEvents,
    WorkflowEvents,
)
from src.logs.events.exceptions import UnknownEventTypeError
from src.logs.events.schema import Actor, Event, EventObject
from src.logs.events.tests.fixtures import make_event, make_smoke_event
from src.utils.logging import SentryLogLevel


def test_emit__enabled__event_in_the_stream(
    fake_stream,
):

    # arrange
    actor = Actor(id=1, email='user@test.test', user_type=UserType.USER)

    # act
    emit(
        event_type=UserEvents.LOGIN,
        account_id=5,
        actor=actor,
        auth_type=AuthTokenType.USER,
        event_object=EventObject(type='user', id=1),
        payload={'source': 'email'},
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == UserEvents.LOGIN
    assert event.category == EventCategory.USERS
    assert event.account_id == 5
    assert event.actor == actor
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(type='user', id=1)
    assert event.payload == {'source': 'email'}


def test_emit__pipeline_off__nothing_written(
    settings,
    fake_stream,
):

    # arrange
    settings.LOGS_BACKEND = LogsBackend.NONE

    # act
    emit(event_type=UserEvents.LOGIN, account_id=5)

    # assert
    assert fake_stream.events == []


def test_emit__unknown_type__raise(
    settings,
    fake_stream,
):

    # arrange
    settings.LOGS_STRICT = True

    # act
    with pytest.raises(UnknownEventTypeError) as ex:
        emit(event_type='nope.nope', account_id=5)

    # assert
    assert str(ex.value) == 'Unknown event type: nope.nope'
    assert fake_stream.events == []


def test_emit__open_transaction__nothing_written_before_commit(
    scheduled_stream,
    mocker,
):

    """ A rolled back transaction publishes nothing: the write waits
        for the commit in an on_commit callback. """

    # arrange
    callbacks = []
    on_commit_mock = mocker.patch(
        'src.logs.events.emitter.transaction.on_commit',
        side_effect=callbacks.append,
    )

    # act
    emit(event_type=UserEvents.LOGIN, account_id=5)

    # assert
    assert scheduled_stream.events == []
    assert len(callbacks) == 1
    on_commit_mock.assert_called_once_with(callbacks[0])


def test_emit__committed_transaction__callback_writes_the_event(
    scheduled_stream,
    mocker,
):

    # arrange
    callbacks = []
    on_commit_mock = mocker.patch(
        'src.logs.events.emitter.transaction.on_commit',
        side_effect=callbacks.append,
    )
    emit(event_type=UserEvents.LOGIN, account_id=5)

    # act
    callbacks[0]()

    # assert
    assert len(scheduled_stream.events) == 1
    assert scheduled_stream.last_event().type == UserEvents.LOGIN
    on_commit_mock.assert_called_once_with(callbacks[0])


def test_emit__stream_error__request_not_broken(
    settings,
    fake_stream,
    mocker,
):

    """ The write runs outside any caller's try block and Django 2.2
        pops the callbacks before calling them: an exception here
        would drop every callback registered after this one. """

    # arrange
    settings.LOGS_SERVICE_NAME = 'pneumatic-test'
    error = redis.ConnectionError('down')
    xadd_mock = mocker.patch.object(
        fake_stream,
        attribute='xadd',
        side_effect=error,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )
    moment = timezone.now()

    # act
    emit(event_type=UserEvents.LOGIN, account_id=5, ts=moment)

    # assert
    xadd_mock.assert_called_once_with(
        Event(
            type=UserEvents.LOGIN,
            category=EventCategory.USERS,
            service='pneumatic-test',
            ts=moment,
            account_id=5,
        ),
    )
    capture_sentry_message_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'ConnectionError', 'dropped': 0},
        level=SentryLogLevel.ERROR,
    )


def test_emit__stream_error_twice__reported_once(
    fake_stream,
    mocker,
):

    """ A Redis outage hits every single request: the log line shows
        all of them, Sentry gets one message a minute. The circuit is
        left closed between the two writes (the clock of the emitter
        is moved past the window) so that both of them reach Redis. """

    # arrange
    error = redis.ConnectionError('down')
    xadd_mock = mocker.patch.object(
        fake_stream,
        attribute='xadd',
        side_effect=error,
    )
    monotonic_mock = mocker.patch(
        'src.logs.events.emitter.monotonic',
        side_effect=[100.0, 100.0 + CIRCUIT_OPEN_SECONDS],
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )

    # act
    emit(event_type=UserEvents.LOGIN, account_id=5)
    emit(event_type=UserEvents.LOGIN, account_id=5)

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'ConnectionError', 'dropped': 0},
        level=SentryLogLevel.ERROR,
    )
    assert xadd_mock.call_count == 2
    xadd_mock.assert_has_calls([
        mocker.call(mocker.ANY),
        mocker.call(mocker.ANY),
    ])
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_emit__misconfigured_url__request_not_broken(
    events_enabled,
    run_on_commit,
    mocker,
):

    """ An empty LOGS_REDIS_URL makes redis-py raise ValueError, which
        is not a RedisError: _write has to catch that one too. """

    # arrange
    error = ValueError('empty url')
    get_stream_mock = mocker.patch(
        'src.logs.events.emitter.get_stream',
        side_effect=error,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )

    # act
    emit(event_type=UserEvents.LOGIN, account_id=5)

    # assert
    get_stream_mock.assert_called_once_with()
    capture_sentry_message_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'ValueError', 'dropped': 0},
        level=SentryLogLevel.ERROR,
    )


def test_write__failed_write__next_write_dropped(mocker):

    """ One failed write opens the circuit: the next write within
        CIRCUIT_OPEN_SECONDS does not touch Redis at all, a request
        must not wait for a buffer that is down. """

    # arrange
    error = redis.ConnectionError('down')
    stream_mock = mocker.Mock()
    stream_mock.xadd.side_effect = error
    get_stream_mock = mocker.patch(
        'src.logs.events.emitter.get_stream',
        return_value=stream_mock,
    )
    monotonic_mock = mocker.patch(
        'src.logs.events.emitter.monotonic',
        side_effect=[100.0, 100.0 + CIRCUIT_OPEN_SECONDS - 0.1],
    )
    report_error_mock = mocker.patch(
        'src.logs.events.emitter.report_error',
    )
    first_event = make_smoke_event(1)
    second_event = make_smoke_event(2)
    _write(event=first_event)

    # act
    _write(event=second_event)

    # assert
    assert emitter_module._circuit.dropped == 1
    assert emitter_module._circuit.is_open(
        now=100.0 + CIRCUIT_OPEN_SECONDS - 0.1,
    )
    get_stream_mock.assert_called_once_with()
    stream_mock.xadd.assert_called_once_with(first_event)
    report_error_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'ConnectionError', 'dropped': 0},
    )
    assert monotonic_mock.call_count == 2
    monotonic_mock.assert_has_calls([mocker.call(), mocker.call()])


def test_write__window_passed__written_and_recovery_logged(
    mocker,
    caplog,
):

    """ After the window the write goes through again, and the log
        says how many events were lost meanwhile. """

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    error = redis.ConnectionError('down')
    stream_mock = mocker.Mock()
    stream_mock.xadd.side_effect = [error, '3-0']
    get_stream_mock = mocker.patch(
        'src.logs.events.emitter.get_stream',
        return_value=stream_mock,
    )
    monotonic_mock = mocker.patch(
        'src.logs.events.emitter.monotonic',
        side_effect=[100.0, 101.0, 100.0 + CIRCUIT_OPEN_SECONDS],
    )
    report_error_mock = mocker.patch(
        'src.logs.events.emitter.report_error',
    )
    first_event = make_smoke_event(1)
    second_event = make_smoke_event(2)
    third_event = make_smoke_event(3)
    _write(event=first_event)
    _write(event=second_event)

    # act
    _write(event=third_event)

    # assert
    assert emitter_module._circuit.dropped == 0
    assert caplog.messages == [
        'Events stream is unavailable: ConnectionError',
        'Events stream is back, events dropped meanwhile: 1',
    ]
    assert get_stream_mock.call_count == 2
    get_stream_mock.assert_has_calls([mocker.call(), mocker.call()])
    assert stream_mock.xadd.call_count == 2
    stream_mock.xadd.assert_has_calls([
        mocker.call(first_event),
        mocker.call(third_event),
    ])
    report_error_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'ConnectionError', 'dropped': 0},
    )
    assert monotonic_mock.call_count == 3
    monotonic_mock.assert_has_calls([
        mocker.call(),
        mocker.call(),
        mocker.call(),
    ])


def test_write__healthy_stream__nothing_logged(mocker, caplog):

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    stream_mock = mocker.Mock()
    stream_mock.xadd.return_value = '1-0'
    get_stream_mock = mocker.patch(
        'src.logs.events.emitter.get_stream',
        return_value=stream_mock,
    )
    report_error_mock = mocker.patch(
        'src.logs.events.emitter.report_error',
    )
    event = make_smoke_event()

    # act
    _write(event=event)

    # assert
    assert caplog.messages == []
    assert emitter_module._circuit.dropped == 0
    get_stream_mock.assert_called_once_with()
    stream_mock.xadd.assert_called_once_with(event)
    report_error_mock.assert_not_called()


def test_report_stream_error__dropped_events__count_in_the_report(
    mocker,
    caplog,
):

    """ Only the class of the error leaves: the text of a Redis error
        may carry the connection URL, and the password with it. """

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    error = redis.ConnectionError(
        'Error connecting to redis://:secret@redis:6379/4',
    )
    monotonic_mock = mocker.patch(
        'src.logs.events.emitter.monotonic',
        return_value=100.0,
    )
    get_stream_mock = mocker.patch('src.logs.events.emitter.get_stream')
    report_error_mock = mocker.patch(
        'src.logs.events.emitter.report_error',
    )
    first_event = make_event()
    second_event = make_event()
    third_event = make_event()
    emitter_module._circuit.trip(now=100.0)
    _write(event=first_event)
    _write(event=second_event)
    _write(event=third_event)

    # act
    _report_stream_error(exc=error)

    # assert
    assert caplog.messages == ['Events stream is unavailable: ConnectionError']
    report_error_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'ConnectionError', 'dropped': 3},
    )
    get_stream_mock.assert_not_called()
    assert monotonic_mock.call_count == 3
    monotonic_mock.assert_has_calls([
        mocker.call(),
        mocker.call(),
        mocker.call(),
    ])


def test_build_event__actor_and_auth_type__written_as_given(
    request_context,
):

    """ Who acts and how they were authenticated come from the
        caller only: the context of the request names neither. """

    # arrange
    actor = Actor(id=3, email='guest@test.test', user_type=UserType.GUEST)

    # act
    event = _build_event(
        event_type=UserEvents.LOGIN,
        account_id=5,
        actor=actor,
        auth_type=AuthTokenType.GUEST,
    )

    # assert
    assert event.actor == actor
    assert event.auth_type == AuthTokenType.GUEST


def test_build_event__no_actor__system_record(request_context):

    """ A task, a callback or an anonymous request: no actor and no
        credential, whatever the context of the request holds. """

    # arrange
    account_id = 5

    # act
    event = _build_event(
        event_type=UserEvents.LOGIN,
        account_id=account_id,
    )

    # assert
    assert event.actor is None
    assert event.auth_type is None


def test_build_event__context__values_from_context(request_context):

    # arrange
    account_id = 5

    # act
    event = _build_event(
        event_type=UserEvents.LOGIN,
        account_id=account_id,
    )

    # assert
    assert event.ip == '9.9.9.9'
    assert event.user_agent == 'Chrome'
    assert event.request_id == 'ctx-request'


def test_build_event__no_context__empty_request_fields():

    # arrange
    account_id = 5

    # act
    event = _build_event(
        event_type=UserEvents.LOGIN,
        account_id=account_id,
    )

    # assert
    assert event.ip is None
    assert event.user_agent is None
    assert event.request_id is None


def test_build_event__registry__category_of_the_type():

    # arrange
    payload = {'target_email': 'target@test.test'}

    # act
    event = _build_event(
        event_type=UserEvents.DEACTIVATE,
        account_id=5,
        payload=payload,
    )

    # assert
    assert event.category == EventCategory.USERS
    assert event.payload == payload


def test_build_event__unknown_type_not_strict__other_category(
    settings,
    mocker,
):

    """ A typo in a running deployment files the event under OTHER
        instead of breaking the request. """

    # arrange
    settings.LOGS_STRICT = False
    report_error_mock = mocker.patch(
        'src.logs.events.registry.report_error',
    )

    # act
    event = _build_event(event_type='nope.nope', account_id=5)

    # assert
    assert event.type == 'nope.nope'
    assert event.category == EventCategory.OTHER
    report_error_mock.assert_called_once_with(
        message='Unknown event type',
        data={'event_type': 'nope.nope'},
        level=SentryLogLevel.WARNING,
        key='unknown-event-type:nope.nope',
    )


def test_build_event__secret_in_the_payload__redacted():

    # arrange
    payload = {'name': 'key', 'token': 'raw-secret'}

    # act
    event = _build_event(
        event_type=ApiKeyEvents.CREATE,
        account_id=5,
        payload=payload,
    )

    # assert
    assert event.payload == {'name': 'key', 'token': '[redacted]'}


def test_build_event__given_ts__used():

    # arrange
    moment = timezone.now()

    # act
    event = _build_event(
        event_type=WorkflowEvents.RUN,
        account_id=5,
        workflow_id=11,
        task_id=22,
        ts=moment,
    )

    # assert
    assert event.ts == moment
    assert event.workflow_id == 11
    assert event.task_id == 22


def test_build_event__no_ts__now(mocker):

    # arrange
    moment = timezone.now()
    now_mock = mocker.patch(
        'src.logs.events.emitter.timezone.now',
        return_value=moment,
    )

    # act
    event = _build_event(event_type=UserEvents.LOGIN, account_id=5)

    # assert
    assert event.ts == moment
    now_mock.assert_called_once_with()


def test_build_event__account_not_given__no_account_marker():

    """ account_id is an index label of the log backend, that is the
        tenant boundary of the journal. None would reach it as the
        literal label "None"; 5.1 of the plan reserves 0 for an event
        without an account, a failed sign in above all. """

    # arrange
    account_id = None

    # act
    event = _build_event(
        event_type=UserEvents.LOGOUT,
        account_id=account_id,
    )

    # assert
    assert event.account_id == NO_ACCOUNT


def test_build_event__settings__service_name_of_the_backend(settings):

    """ The stream is shared with the file service: every record
        names its writer, the sink no longer assumes the backend. """

    # arrange
    settings.LOGS_SERVICE_NAME = 'pneumatic-test'

    # act
    event = _build_event(
        event_type=UserEvents.LOGIN,
        account_id=5,
    )

    # assert
    assert event.service == 'pneumatic-test'


def test_emit__patched_name__the_one_the_callers_import():

    """ The tests of the services and the views patch
        src.logs.events.services.emit: a module that imported the
        function from the package instead would leave those patches
        intercepting nothing, and every "no event" assert would pass
        for the wrong reason. """

    # arrange
    name = 'emit'

    # act
    services_emit = getattr(services_module, name)

    # assert
    assert services_emit is emit
