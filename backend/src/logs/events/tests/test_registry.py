from unittest.mock import call

import pytest

from src.logs.events import registry as registry_module
from src.logs.events.adapters.workflow import WORKFLOW_EVENT_TYPE_NAMES
from src.logs.events.enums import EventCategory, EventName
from src.logs.events.exceptions import (
    EventsError,
    UnknownEventTypeError,
)
from src.logs.events.registry import (
    ACTOR_PII,
    EVENT_TYPES,
    REGISTRY,
    EventType,
    resolve_event_type,
    validate_registry,
)
from src.logs.events.tests.fakes import event_name_values
from src.utils.logging import SentryLogLevel


def test_validate_registry__shipped_declaration__ok():

    # act
    validate_registry()

    # assert
    assert len(REGISTRY) == len(EVENT_TYPES)


def test_validate_registry__duplicated_name__raise(mocker):

    # arrange
    mocker.patch.object(
        registry_module,
        'EVENT_TYPES',
        (
            EventType(name='user.login', category=EventCategory.AUDIT),
            EventType(name='user.login', category=EventCategory.AUDIT),
        ),
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == 'Duplicated event type: user.login'


def test_validate_registry__name_without_domain__raise(mocker):

    # arrange
    mocker.patch.object(
        registry_module,
        'EVENT_TYPES',
        (EventType(name='user_login', category=EventCategory.AUDIT),),
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == 'Invalid event type name: user_login'


def test_validate_registry__undeclared_category__raise(mocker):

    # arrange
    mocker.patch.object(
        registry_module,
        'EVENT_TYPES',
        (EventType(name='user.login', category='loud'),),
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == (
        'Invalid category "loud" of the event type: user.login'
    )


def test_validate_registry__pii_path_of_unknown_field__raise(mocker):

    # arrange
    mocker.patch.object(
        registry_module,
        'EVENT_TYPES',
        (
            EventType(
                name='user.login',
                category=EventCategory.AUDIT,
                pii=('workflow_id.value',),
            ),
        ),
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == (
        'Invalid pii path "workflow_id.value" of the event type: '
        'user.login'
    )


def test_validate_registry__pii_namespace_without_field__raise(mocker):

    # arrange
    mocker.patch.object(
        registry_module,
        'EVENT_TYPES',
        (
            EventType(
                name='user.login',
                category=EventCategory.AUDIT,
                pii=('payload',),
            ),
        ),
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == (
        'Invalid pii path "payload" of the event type: user.login'
    )


def test_validate_registry__every_pii_form__ok(mocker):

    # arrange
    mocker.patch.object(
        registry_module,
        'EVENT_TYPES',
        (
            EventType(
                name='user.login',
                category=EventCategory.AUDIT,
                pii=(
                    'ip',
                    'user_agent',
                    'actor.email',
                    'object.id',
                    'payload.target_email',
                ),
            ),
        ),
    )

    # act
    result = validate_registry()

    # assert
    assert result is None


def test_registry__event_names__one_declaration_per_constant():

    """ EventName is the list of the types the code emits, the
        registry is the list of the types the pipeline accepts: a
        constant without a declaration fails every emit under
        LOGS_STRICT, a declaration without a constant is dead. """

    # arrange
    names = event_name_values()

    # act
    declared = set(REGISTRY)

    # assert
    assert declared == names
    assert len(EVENT_TYPES) == len(REGISTRY)


@pytest.mark.parametrize('name', sorted(WORKFLOW_EVENT_TYPE_NAMES.values()))
def test_registry__workflow_type__declares_the_names_as_personal(name):

    """ The adapter puts workflow_name and task_name into the payload
        of all 24 mapped types, and both routinely carry a person's
        name. A type that does not declare them sends them as plain
        attributes past the redaction rule of the collector. """

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.workflow_name',
        'payload.task_name',
    )


def test_registry__login_as__reason_declared_as_personal():

    """ The reason is free text typed by a staff member: it names
        people and tickets as often as not. """

    # act
    event_type = REGISTRY[EventName.USER_LOGIN_AS]

    # assert
    assert event_type.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
        'payload.reason',
    )
    assert event_type.category == EventCategory.AUDIT


def test_registry__template_clone__activity_with_the_name_as_personal():

    # act
    event_type = REGISTRY[EventName.TEMPLATE_CLONE]

    # assert
    assert event_type.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.name',
    )
    assert event_type.category == EventCategory.ACTIVITY


@pytest.mark.parametrize(
    'name',
    (
        EventName.FILE_UPLOAD,
        EventName.FILE_DOWNLOAD,
        EventName.FILE_ACCESS_DENIED,
    ),
)
def test_registry__file_type__audit_with_the_filename_as_personal(name):

    """ The file service writes these records; the sink asks this
        registry for the personal fields, so the declaration here is
        what keeps the file name out of an external backend. """

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.category == EventCategory.AUDIT
    assert event_type.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.filename',
    )


def test_resolve__unknown_type_in_strict_mode__raise(settings):

    # arrange
    settings.LOGS_STRICT = True

    # act
    with pytest.raises(UnknownEventTypeError) as ex:
        resolve_event_type('nope.nope')

    # assert
    assert str(ex.value) == 'Unknown event type: nope.nope'


def test_resolve__unknown_type_in_running_deployment__debug_category(
    mocker,
    settings,
):

    """ A typo must not break a user request outside the strict
        configurations, and the personal fields of the actor are kept
        declared: an empty list would send them as plain attributes. """

    # arrange
    settings.LOGS_STRICT = False
    report_error_mock = mocker.patch(
        'src.logs.events.registry.report_error',
    )

    # act
    event_type = resolve_event_type('nope.nope')

    # assert
    assert event_type.name == 'nope.nope'
    assert event_type.category == EventCategory.DEBUG
    assert event_type.pii == ACTOR_PII
    report_error_mock.assert_called_once_with(
        message='Unknown event type',
        data={'event_type': 'nope.nope'},
        level=SentryLogLevel.WARNING,
        key='unknown-event-type:nope.nope',
    )


def test_resolve__two_unknown_types__reported_under_their_own_keys(
    mocker,
    settings,
):

    """ The throttle lives in report_error and buckets by key, so the
        key has to name the type: one silent type must not hide the
        next one. """

    # arrange
    settings.LOGS_STRICT = False
    report_error_mock = mocker.patch(
        'src.logs.events.registry.report_error',
    )

    # act
    resolve_event_type('nope.nope')
    resolve_event_type('other.other')

    # assert
    assert report_error_mock.call_count == 2
    report_error_mock.assert_has_calls([
        call(
            message='Unknown event type',
            data={'event_type': 'nope.nope'},
            level=SentryLogLevel.WARNING,
            key='unknown-event-type:nope.nope',
        ),
        call(
            message='Unknown event type',
            data={'event_type': 'other.other'},
            level=SentryLogLevel.WARNING,
            key='unknown-event-type:other.other',
        ),
    ])


@pytest.mark.parametrize(
    ('name', 'pii'),
    (
        (
            EventName.USER_PASSWORD_RESET_REQUEST,
            ('actor.email', 'ip', 'user_agent', 'payload.target_email'),
        ),
        (EventName.USER_PASSWORD_RESET, ('actor.email', 'ip', 'user_agent')),
        (EventName.USER_PASSWORD_CHANGE, ('actor.email', 'ip', 'user_agent')),
        (EventName.ACCOUNT_UPDATE, ('actor.email', 'ip', 'user_agent')),
        (
            EventName.USER_CREATE,
            ('actor.email', 'ip', 'user_agent', 'payload.target_email'),
        ),
        (EventName.USER_TRANSFER, ('actor.email', 'ip', 'user_agent')),
        (
            EventName.INVITE_CREATE,
            ('actor.email', 'ip', 'user_agent', 'payload.target_email'),
        ),
        (
            EventName.INVITE_RESEND,
            ('actor.email', 'ip', 'user_agent', 'payload.target_email'),
        ),
    ),
)
def test_registry__account_and_password_type__audit_with_declared_pii(
    name,
    pii,
):

    """ The address of the person an admin or a guest acts upon is
        personal data like the address of the actor. """

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.category == EventCategory.AUDIT
    assert event_type.pii == pii
