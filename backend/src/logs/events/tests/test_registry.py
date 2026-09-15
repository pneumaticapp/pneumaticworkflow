import pytest

from src.logs.events import registry as registry_module
from src.logs.events.adapters.workflow import WORKFLOW_EVENT_TYPE_NAMES
from src.logs.events.enums import (
    EVENT_CLASSES,
    EventCategory,
    FileEvents,
    TemplateEvents,
    UserEvents,
)
from src.logs.events.exceptions import (
    EventsError,
    UnknownEventTypeError,
)
from src.logs.events.registry import (
    EVENT_TYPES,
    REGISTRY,
    EventType,
    resolve_event_type,
    validate_registry,
)
from src.logs.events.tests.fixtures import event_name_values
from src.utils.logging import SentryLogLevel


def test_validate_registry__shipped_declaration__ok():

    # arrange
    declared = len(EVENT_TYPES)

    # act
    validate_registry()

    # assert
    assert len(REGISTRY) == declared


def test_validate_registry__duplicated_name__raise(mocker):

    # arrange
    event_types = (
        EventType(name='user.login', category=EventCategory.USERS),
        EventType(name='user.login', category=EventCategory.USERS),
    )
    mocker.patch.object(
        registry_module,
        attribute='EVENT_TYPES',
        new=event_types,
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == 'Duplicated event type: user.login'


def test_validate_registry__name_without_domain__raise(mocker):

    # arrange
    event_types = (
        EventType(name='user_login', category=EventCategory.USERS),
    )
    mocker.patch.object(
        registry_module,
        attribute='EVENT_TYPES',
        new=event_types,
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == 'Invalid event type name: user_login'


def test_validate_registry__name_with_trailing_newline__raise(mocker):

    """ The whole name has to match: "$" of a plain match would let
        a trailing newline through. """

    # arrange
    event_types = (
        EventType(name='user.login\n', category=EventCategory.USERS),
    )
    mocker.patch.object(
        registry_module,
        attribute='EVENT_TYPES',
        new=event_types,
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == 'Invalid event type name: user.login\n'


def test_validate_registry__undeclared_category__raise(mocker):

    # arrange
    event_types = (EventType(name='user.login', category='loud'),)
    mocker.patch.object(
        registry_module,
        attribute='EVENT_TYPES',
        new=event_types,
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == (
        'Invalid category "loud" of the event type: user.login'
    )


def test_validate_registry__constant_without_a_row__raise(mocker):

    """ A constant of an events class that the table does not
        declare would fail every emit under LOGS_STRICT: the start
        of the process has to name it. """

    # arrange
    event_types = tuple(
        event_type for event_type in EVENT_TYPES
        if event_type.name != UserEvents.LOGIN
    )
    mocker.patch.object(
        registry_module,
        attribute='EVENT_TYPES',
        new=event_types,
    )

    # act
    with pytest.raises(EventsError) as ex:
        validate_registry()

    # assert
    assert str(ex.value) == (
        'Event type user.login of UserEvents is not declared '
        'in the registry'
    )


def test_registry__event_names__one_declaration_per_constant():

    """ The events classes list the types the code emits, the
        registry lists the types the pipeline accepts: a constant
        without a declaration fails every emit under LOGS_STRICT, a
        declaration without a constant is dead. """

    # arrange
    names = event_name_values()

    # act
    declared = set(REGISTRY)

    # assert
    assert declared == names
    assert len(EVENT_TYPES) == len(REGISTRY)


@pytest.mark.parametrize('events_class', EVENT_CLASSES)
def test_registry__events_class__category_of_the_class(events_class):

    # arrange
    names = event_name_values() & set(vars(events_class).values())

    # act
    categories = {REGISTRY[name].category for name in names}

    # assert
    assert categories == {events_class.CATEGORY}


@pytest.mark.parametrize('name', sorted(WORKFLOW_EVENT_TYPE_NAMES.values()))
def test_registry__workflow_type__described(name):

    """ The adapter maps all 24 workflow event types onto a declared
        type of the workflows or the tasks category. """

    # arrange
    categories = {EventCategory.WORKFLOWS, EventCategory.TASKS}

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.category in categories
    assert event_type.description != ''


def test_registry__login_as__users_category():

    # arrange
    name = UserEvents.LOGIN_AS

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.category == EventCategory.USERS
    assert event_type.description == 'Superuser signed in as a user'


def test_registry__template_clone__templates_category():

    # arrange
    name = TemplateEvents.CLONE

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.category == EventCategory.TEMPLATES


@pytest.mark.parametrize(
    'name',
    (
        FileEvents.UPLOAD,
        FileEvents.DOWNLOAD,
        FileEvents.ACCESS_DENIED,
    ),
)
def test_registry__file_type__files_category(name):

    """ The file service writes these records into the same stream;
        the backend declares them so that the consumer files them
        under a category of their own. """

    # arrange
    expected_category = EventCategory.FILES

    # act
    event_type = REGISTRY[name]

    # assert
    assert event_type.category == expected_category


def test_resolve__unknown_type_in_strict_mode__raise(settings):

    # arrange
    settings.LOGS_STRICT = True
    name = 'nope.nope'

    # act
    with pytest.raises(UnknownEventTypeError) as ex:
        resolve_event_type(name=name)

    # assert
    assert str(ex.value) == 'Unknown event type: nope.nope'


def test_resolve__unknown_type_in_running_deployment__other_category(
    mocker,
    settings,
):

    """ A typo must not break a user request outside the strict
        configurations: the event is filed under OTHER and the type
        is reported. """

    # arrange
    settings.LOGS_STRICT = False
    name = 'nope.nope'
    report_error_mock = mocker.patch(
        'src.logs.events.registry.report_error',
    )

    # act
    event_type = resolve_event_type(name=name)

    # assert
    assert event_type == EventType(
        name='nope.nope',
        category=EventCategory.OTHER,
    )
    assert event_type.description == ''
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
    first_name = 'nope.nope'
    second_name = 'other.other'
    report_error_mock = mocker.patch(
        'src.logs.events.registry.report_error',
    )

    # act
    resolve_event_type(name=first_name)
    resolve_event_type(name=second_name)

    # assert
    assert report_error_mock.call_count == 2
    report_error_mock.assert_has_calls([
        mocker.call(
            message='Unknown event type',
            data={'event_type': 'nope.nope'},
            level=SentryLogLevel.WARNING,
            key='unknown-event-type:nope.nope',
        ),
        mocker.call(
            message='Unknown event type',
            data={'event_type': 'other.other'},
            level=SentryLogLevel.WARNING,
            key='unknown-event-type:other.other',
        ),
    ])
