import pytest
import redis
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from src.authentication.enums import AuthTokenType
from src.logs.events.entities import Actor
from src.logs.events.enums import EventCategory, UserEvents
from src.logs.events.services import AuditEventService
from src.logs.events.tests.fixtures import make_event

pytestmark = pytest.mark.django_db


def test_event__request_context__readable_record(
    fake_stream,
    request_context,
    event_kwargs,
):

    # arrange

    # act
    AuditEventService._event(**event_kwargs)
    event = fake_stream.last_event()

    # assert
    assert event.type == UserEvents.LOGIN
    assert event.category == EventCategory.USERS
    assert event.service == 'pneumatic-backend'
    # The caller decides the tenant, independently of the actor's account.
    assert event.account_id == event_kwargs['account_id']
    assert event.account_name == 'Operations'
    assert event.actor == Actor(
        id=event_kwargs['user'].id,
        email='actor@test.test',
        user_type='user',
    )
    assert event.object.name == 'actor@test.test'
    assert event.auth_type == AuthTokenType.USER
    assert event.payload == {'source': 'email', 'password': '[redacted]'}
    assert (event.ip, event.user_agent, event.request_id) == (
        '9.9.9.9',
        'Chrome',
        'ctx-request',
    )


def test_event__disabled__nothing_emitted(settings, fake_stream, event_kwargs):

    # arrange
    settings.LOGS_BACKEND = None

    # act
    AuditEventService._event(**event_kwargs)

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, ''])
def test_event__disabled__metadata_not_evaluated(
    settings,
    fake_stream,
    event_kwargs,
    mocker,
    backend,
):
    """Every deferred field remains untouched while the journal is off."""

    # arrange
    metadata_mock = mocker.Mock()
    event_kwargs.update(
        account_id=metadata_mock,
        object_id=metadata_mock,
        workflow_id=metadata_mock,
        task_id=metadata_mock,
        payload=metadata_mock,
        object_name=metadata_mock,
        account_name=metadata_mock,
    )
    settings.LOGS_BACKEND = backend

    # act
    AuditEventService._event(**event_kwargs)

    # assert
    metadata_mock.assert_not_called()
    assert fake_stream.events == []


@pytest.mark.django_db(transaction=True)
def test_event__deferred_metadata__snapshot_before_commit(
    scheduled_stream,
    event_kwargs,
):
    """Delayed Redis delivery does not delay resolving the event values."""

    # arrange
    account_id = event_kwargs['account_id']
    state = {
        'account_id': account_id,
        'object_id': 7,
        'workflow_id': 8,
        'task_id': 9,
        'name': 'Before',
        'payload': {'state': 'before'},
    }
    event_kwargs.update(
        account_id=lambda: state['account_id'],
        object_id=lambda: state['object_id'],
        workflow_id=lambda: state['workflow_id'],
        task_id=lambda: state['task_id'],
        payload=lambda: state['payload'],
        object_name=lambda: state['name'],
        account_name=lambda: state['name'],
    )

    # act
    with transaction.atomic():
        AuditEventService._event(**event_kwargs)
        events_before_commit = list(scheduled_stream.events)
        state.update(account_id=0, object_id=0, workflow_id=0, task_id=0)
        state['name'] = 'After'
        state['payload']['state'] = 'after'
    event = scheduled_stream.last_event()

    # assert
    assert events_before_commit == []
    assert event.account_id == account_id
    assert event.object.id == 7
    assert event.workflow_id == 8
    assert event.task_id == 9
    assert event.object.name == 'Before'
    assert event.account_name == 'Before'
    assert event.payload == {'state': 'before'}


@pytest.mark.parametrize(
    ('name', 'value'),
    [
        ('LOGS_BACKEND', 'unknown'),
        ('LOGS_REDIS_URL', None),
        ('LOGS_REDIS_URL', ''),
        ('LOGS_REDIS_URL', 'http://localhost'),
        ('LOGS_REDIS_URL', 'redis://localhost:bad'),
        ('LOGS_REDIS_URL', 'unix://'),
        ('LOGS_OTLP_ENDPOINT', None),
        ('LOGS_OTLP_ENDPOINT', ''),
        ('LOGS_OTLP_ENDPOINT', 'undefined'),
        ('LOGS_OTLP_ENDPOINT', 17),
        ('LOGS_OTLP_ENDPOINT', 'redis://localhost'),
        ('LOGS_OTLP_ENDPOINT', 'https://host:bad'),
        ('LOGS_OTLP_ENDPOINT', 'https://host?token=secret'),
        ('LOGS_OTLP_ENDPOINT', 'https://host#fragment'),
        ('LOGS_OTLP_ENDPOINT', 'https://host?'),
        ('LOGS_OTLP_ENDPOINT', 'https://host#'),
        ('LOGS_STREAM_MAXLEN', None),
        ('LOGS_STREAM_MAXLEN', 0),
        ('LOGS_STREAM_MAXLEN', -1),
        ('LOGS_STREAM_MAXLEN', '10'),
        ('LOGS_CONSUMER_BATCH_SIZE', None),
        ('LOGS_CONSUMER_BATCH_SIZE', 0),
        ('LOGS_CONSUMER_BATCH_SIZE', -1),
        ('LOGS_CONSUMER_BATCH_SIZE', True),
    ],
)
def test_ready__invalid_setting__raises(
    settings,
    fake_stream,
    name,
    value,
):

    # arrange
    setattr(settings, name, value)

    # act
    with pytest.raises(ImproperlyConfigured, match=name):
        apps.get_app_config('logs').ready()

    # assert
    assert fake_stream.events == []


def test_ready__journal_enabled__valid_configuration_accepted(
    fake_stream,
):

    # arrange

    # act
    apps.get_app_config('logs').ready()

    # assert
    assert fake_stream.events == []


@pytest.mark.parametrize('backend', [None, '', False])
def test_ready__journal_disabled__configuration_not_validated(
    settings,
    backend,
):

    # arrange
    settings.LOGS_BACKEND = backend
    settings.LOGS_REDIS_URL = None

    # act
    apps.get_app_config('logs').ready()

    # assert
    assert settings.LOGS_REDIS_URL is None


def test_event__invalid_configuration__not_validated_per_event(
    settings,
    fake_stream,
    event_kwargs,
):
    """The configuration is validated once at startup, not on every
    event of a running process."""

    # arrange
    settings.LOGS_OTLP_ENDPOINT = None

    # act
    AuditEventService._event(**event_kwargs)

    # assert
    assert len(fake_stream.events) == 1


def test_event__system_action__credentials_cleared(fake_stream, event_kwargs):

    # arrange
    event_kwargs['user'] = None

    # act
    AuditEventService._event(**event_kwargs)
    event = fake_stream.last_event()

    # assert
    assert event.actor is None
    assert event.auth_type is None
    assert event.account_id == event_kwargs['account_id']
    assert event.ip is None


@pytest.mark.django_db(transaction=True)
def test_event__transaction_commit__deferred_write(
    scheduled_stream,
    event_kwargs,
):

    # arrange

    # act
    with transaction.atomic():
        AuditEventService._event(**event_kwargs)
        events_before_commit = list(scheduled_stream.events)

    # assert
    assert events_before_commit == []
    assert len(scheduled_stream.events) == 1


@pytest.mark.django_db(transaction=True)
def test_event__transaction_rollback__callback_discarded(
    scheduled_stream,
    event_kwargs,
):

    # arrange

    # act
    with pytest.raises(ValueError, match='rollback'), transaction.atomic():
        AuditEventService._event(**event_kwargs)
        raise ValueError('rollback')

    # assert
    assert scheduled_stream.events == []


@pytest.mark.django_db(transaction=True)
def test_write__redis_failure__later_callbacks_preserved(
    scheduled_stream,
    mocker,
    event_kwargs,
):

    # arrange
    attempted_events = []

    def fail_write(*, event):
        attempted_events.append(event)
        raise redis.RedisError

    xadd_mock = mocker.patch.object(
        scheduled_stream,
        'xadd',
        side_effect=fail_write,
    )
    later = mocker.Mock()

    # act
    with transaction.atomic():
        AuditEventService._event(**event_kwargs)
        transaction.on_commit(later)

    # assert
    xadd_mock.assert_called_once_with(event=attempted_events[0])
    later.assert_called_once_with()


def test_write__outage_and_recovery__circuit_without_secrets(
    scheduled_stream,
    mocker,
    caplog,
):

    # arrange
    monotonic_mock = mocker.patch(
        'src.logs.events.services.monotonic',
        side_effect=[1, 2, 17],
    )
    xadd = mocker.patch.object(
        scheduled_stream,
        'xadd',
        side_effect=[
            redis.RedisError('redis://user:secret@host'),
            '1-0',
        ],
    )
    report = mocker.patch(
        'src.logs.events.services.capture_sentry_message_throttled',
    )
    event = make_event()

    # act
    AuditEventService._write(event=event)
    AuditEventService._write(event=event)
    dropped_during_outage = AuditEventService._dropped
    AuditEventService._write(event=event)

    # assert
    assert AuditEventService._dropped == 0
    assert dropped_during_outage == 1
    assert xadd.call_count == 2
    xadd.assert_has_calls(
        [
            mocker.call(event=event),
            mocker.call(event=event),
        ],
    )
    assert monotonic_mock.call_count == 3
    monotonic_mock.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ],
    )
    report.assert_called_once_with(
        message='Events stream is unavailable',
        data={'error': 'RedisError', 'dropped': 0},
    )
    assert 'secret' not in caplog.text
