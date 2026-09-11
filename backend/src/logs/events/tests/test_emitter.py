import logging
from time import monotonic

import pytest
import redis
from django.utils import timezone

from src.authentication.enums import AuthTokenType
from src.logs.enums import LogsBackend
from src.logs.events import emitter as emitter_module
from src.logs.events import mixins as mixins_module
from src.logs.events import services as services_module
from src.logs.events.emitter import (
    CIRCUIT_OPEN_SECONDS,
    NO_ACCOUNT,
    _build_event,
    _report_stream_error,
    _write,
    _present_pii,
    emit,
)
from src.logs.events.enums import ActorType, EventCategory, EventName
from src.logs.events.exceptions import UnknownEventTypeError
from src.logs.events.registry import (
    ACTOR_PII,
    EventType,
)
from src.logs.events.schema import Actor, EventObject
from src.logs.events.tests.fakes import make_event, make_smoke_event
from src.utils.logging import SentryLogLevel


def test_emit__enabled__event_in_the_stream(
    fake_stream,
):

    # arrange
    actor = Actor(type=ActorType.USER, id=1, email='user@test.test')

    # act
    emit(
        EventName.USER_LOGIN,
        account_id=5,
        actor=actor,
        event_object=EventObject(type='user', id=1),
        payload={'source': 'email'},
    )

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_LOGIN
    assert event.category == EventCategory.AUDIT
    assert event.account_id == 5
    assert event.actor == actor
    assert event.object == EventObject(type='user', id=1)
    assert event.payload == {'source': 'email'}


def test_emit__pipeline_off__nothing_written(
    settings,
    fake_stream,
):

    # arrange
    settings.LOGS_BACKEND = LogsBackend.NONE

    # act
    emit(EventName.USER_LOGIN, account_id=5)

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
        emit('nope.nope', account_id=5)

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
    emit(EventName.USER_LOGIN, account_id=5)

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
    emit(EventName.USER_LOGIN, account_id=5)

    # act
    callbacks[0]()

    # assert
    assert len(scheduled_stream.events) == 1
    assert scheduled_stream.last_event().type == EventName.USER_LOGIN
    on_commit_mock.assert_called_once_with(callbacks[0])


def test_emit__stream_error__request_not_broken(
    fake_stream,
    mocker,
):

    """ The write runs outside any caller's try block and Django 2.2
        pops the callbacks before calling them: an exception here
        would drop every callback registered after this one. """

    # arrange
    error = redis.ConnectionError('down')
    xadd_mock = mocker.patch.object(
        fake_stream, 'xadd', side_effect=error,
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )
    moment = timezone.now()

    # act
    emit(EventName.USER_LOGIN, account_id=5, ts=moment)

    # assert
    xadd_mock.assert_called_once_with(
        _build_event(EventName.USER_LOGIN, account_id=5, ts=moment),
    )
    capture_sentry_message_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': repr(error), 'dropped': 0},
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
        fake_stream, 'xadd', side_effect=error,
    )
    monotonic_mock = mocker.patch(
        'src.logs.events.emitter.monotonic',
        side_effect=[100.0, 100.0 + CIRCUIT_OPEN_SECONDS],
    )
    capture_sentry_message_mock = mocker.patch(
        'src.logs.events.reporting.capture_sentry_message',
    )

    # act
    emit(EventName.USER_LOGIN, account_id=5)
    emit(EventName.USER_LOGIN, account_id=5)

    # assert
    capture_sentry_message_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': repr(error), 'dropped': 0},
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
    emit(EventName.USER_LOGIN, account_id=5)

    # assert
    get_stream_mock.assert_called_once_with()
    capture_sentry_message_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': repr(error), 'dropped': 0},
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
    _write(first_event)

    # act
    _write(second_event)

    # assert
    assert emitter_module._circuit.dropped == 1
    assert emitter_module._circuit.is_open(100.0 + CIRCUIT_OPEN_SECONDS - 0.1)
    get_stream_mock.assert_called_once_with()
    stream_mock.xadd.assert_called_once_with(first_event)
    report_error_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': repr(error), 'dropped': 0},
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
    _write(first_event)
    _write(second_event)

    # act
    _write(third_event)

    # assert
    assert emitter_module._circuit.dropped == 0
    assert caplog.messages == [
        f'Events stream is unavailable: {error}',
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
        data={'error': repr(error), 'dropped': 0},
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
    _write(event)

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

    # arrange
    caplog.set_level(logging.WARNING, logger='pneumatic.events')
    error = redis.ConnectionError('down')
    report_error_mock = mocker.patch(
        'src.logs.events.emitter.report_error',
    )
    emitter_module._circuit.trip(monotonic())
    for _ in range(3):
        _write(make_event())

    # act
    _report_stream_error(error)

    # assert
    assert caplog.messages == [f'Events stream is unavailable: {error}']
    report_error_mock.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': repr(error), 'dropped': 3},
    )


def test_build_event__explicit_actor__wins(
    request_context,
    request_factory,
    mocker,
):

    # arrange
    actor = Actor(type=ActorType.SYSTEM)
    request = request_factory.get('/')
    request.user = mocker.Mock(
        is_authenticated=True,
        id=1,
        email='user@test.test',
    )

    # act
    event = _build_event(
        EventName.USER_LOGIN,
        account_id=5,
        actor=actor,
        request=request,
    )

    # assert
    assert event.actor == actor


def test_build_event__request_user__actor_from_the_request(
    request_context,
    request_factory,
    mocker,
):

    """ Deviation from 5.1 of the plan: the specification keeps the
        e-mail for the user actor only, the emitter fills it for an
        api_key too. The address is the one of the key owner and it
        is declared personal, so it leaves in the pii.* namespace. """

    # arrange
    request = request_factory.get('/')
    request.user = mocker.Mock(
        is_authenticated=True,
        id=3,
        email='req@test.test',
    )
    request.token_type = AuthTokenType.API

    # act
    event = _build_event(
        EventName.USER_LOGIN,
        account_id=5,
        request=request,
    )

    # assert
    assert event.actor == Actor(
        type=ActorType.API_KEY,
        id=3,
        email='req@test.test',
    )


def test_build_event__anonymous_request__actor_from_the_context(
    request_context,
    request_factory,
    mocker,
):

    # arrange
    request = request_factory.get('/')
    request.user = mocker.Mock(is_authenticated=False)

    # act
    event = _build_event(
        EventName.USER_LOGIN,
        account_id=5,
        request=request,
    )

    # assert
    assert event.actor == Actor(
        type=ActorType.USER,
        id=77,
        email='ctx@test.test',
    )


def test_build_event__no_request_no_context__system_actor():

    # act
    event = _build_event(EventName.USER_LOGIN, account_id=5)

    # assert
    assert event.actor == Actor(type=ActorType.SYSTEM)


def test_build_event__request__ip_and_agent_from_the_request(
    request_context,
    request_factory,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )
    request.request_id = 'req-1'

    # act
    event = _build_event(
        EventName.USER_LOGIN,
        account_id=5,
        request=request,
    )

    # assert
    assert event.ip == '1.2.3.4'
    assert event.user_agent == 'Firefox'
    assert event.request_id == 'req-1'


def test_build_event__request_without_headers__values_from_context(
    request_context,
    request_factory,
):

    """ A Celery request object or a call made deep in a service still
        gets the address of the request being handled. """

    # arrange
    request = request_factory.get('/')
    request.META.pop('REMOTE_ADDR', None)

    # act
    event = _build_event(
        EventName.USER_LOGIN,
        account_id=5,
        request=request,
    )

    # assert
    assert event.ip == '9.9.9.9'
    assert event.user_agent == 'Chrome'
    assert event.request_id == 'ctx-request'


def test_build_event__no_request__values_from_context(request_context):

    # act
    event = _build_event(EventName.USER_LOGIN, account_id=5)

    # assert
    assert event.ip == '9.9.9.9'
    assert event.user_agent == 'Chrome'
    assert event.request_id == 'ctx-request'


def test_build_event__no_request_no_context__empty_request_fields():

    # act
    event = _build_event(EventName.USER_LOGIN, account_id=5)

    # assert
    assert event.ip is None
    assert event.user_agent is None
    assert event.request_id is None


def test_build_event__registry__category_and_present_pii():

    # act
    event = _build_event(
        EventName.USER_DEACTIVATE,
        account_id=5,
        actor=Actor(type=ActorType.SYSTEM),
        payload={'target_email': 'target@test.test'},
    )

    # assert
    assert event.category == EventCategory.AUDIT
    assert event.pii == ('payload.target_email',)


def test_build_event__filled_fields__all_declared_pii(
    request_context,
    request_factory,
    mocker,
):

    # arrange
    request = request_factory.get(
        '/',
        HTTP_X_REAL_IP='1.2.3.4',
        HTTP_USER_AGENT='Firefox',
    )
    request.user = mocker.Mock(
        is_authenticated=True,
        id=1,
        email='actor@test.test',
    )

    # act
    event = _build_event(
        EventName.USER_DEACTIVATE,
        account_id=5,
        request=request,
        payload={'target_email': 'target@test.test'},
    )

    # assert
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
    )


def test_build_event__type_without_declared_actor_pii__pii_added(
    request_context,
    mocker,
):

    """ The e-mail, the address and the user agent belong to whoever
        made the request whatever the type is, and a type that forgot
        to declare them would leak them as plain attributes. """

    # arrange
    mocker.patch.dict(
        'src.logs.events.registry.REGISTRY',
        {
            'system.test': EventType(
                name='system.test',
                category=EventCategory.DEBUG,
            ),
        },
    )

    # act
    event = _build_event('system.test', account_id=5)

    # assert
    assert event.pii == ACTOR_PII


def test_build_event__unresolvable_pii_path__dropped(
    request_context,
    mocker,
):

    """ A path no field of the event answers is not reported as
        personal data that left the system. """

    # arrange
    mocker.patch.dict(
        'src.logs.events.registry.REGISTRY',
        {
            'system.test': EventType(
                name='system.test',
                category=EventCategory.DEBUG,
                pii=('workflow_id.value',),
            ),
        },
    )

    # act
    event = _build_event('system.test', account_id=5)

    # assert
    assert event.pii == ACTOR_PII


def test_build_event__secret_in_the_payload__redacted():

    # act
    event = _build_event(
        EventName.API_KEY_CREATE,
        account_id=5,
        payload={'name': 'key', 'token': 'raw-secret'},
    )

    # assert
    assert event.payload == {'name': 'key', 'token': '[redacted]'}


def test_build_event__given_ts__used():

    # arrange
    moment = timezone.now()

    # act
    event = _build_event(
        EventName.WORKFLOW_RUN,
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
    event = _build_event(EventName.USER_LOGIN, account_id=5)

    # assert
    assert event.ts == moment
    now_mock.assert_called_once_with()


def test_build_event__account_not_given__no_account_marker():

    """ account_id is an index label of the log backend, that is the
        tenant boundary of the journal. None would reach it as the
        literal label "None"; 5.1 of the plan reserves 0 for an event
        without an account, a failed sign in above all. """

    # act
    event = _build_event(EventName.USER_LOGOUT, account_id=None)

    # assert
    assert event.account_id == NO_ACCOUNT


def test_build_event__settings__service_name_of_the_backend(settings):

    """ The stream is shared with the file service: every record
        names its writer, the sink no longer assumes the backend. """

    # arrange
    settings.LOGS_SERVICE_NAME = 'pneumatic-test'

    # act
    event = _build_event(
        EventName.USER_LOGIN,
        account_id=5,
        actor=Actor(type=ActorType.SYSTEM),
    )

    # assert
    assert event.service == 'pneumatic-test'


def test_present_pii__empty_string__not_listed():

    """ The list is the audit answer to "what left": an empty user
        agent is nothing that left. """

    # arrange
    event = make_event(user_agent='', ip=None)

    # act
    result = _present_pii(('actor.email', 'ip', 'user_agent'), event)

    # assert
    assert result == ('actor.email',)


def test_emit__patched_name__the_one_the_callers_import():

    """ The tests of the services and the views patch
        src.logs.events.services.emit and src.logs.events.mixins.emit:
        a module that imported the function from the package instead
        would leave those patches intercepting nothing, and every
        "no event" assert would pass for the wrong reason. """

    # assert
    assert services_module.emit is emit
    assert mixins_module.emit is emit
