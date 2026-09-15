import pytest

from src.logs.events.enums import (
    EVENT_CLASSES,
    AccountEvents,
    EventCategory,
    UserEvents,
    event_names_of,
)


def test_event_names_of__events_class__constants_without_category():

    # arrange
    events_class = AccountEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert names == (
        'account.update',
        'account.verify',
        'account.verification_resend',
        'tenant.create',
        'tenant.delete',
        'tenant.login_as',
    )


def test_event_names_of__invites_class__invites_among_user_events():

    # arrange
    events_class = UserEvents

    # act
    names = event_names_of(events_class=events_class)

    # assert
    assert 'user.login' in names
    assert 'invite.create' in names
    assert EventCategory.USERS not in names


@pytest.mark.parametrize('events_class', EVENT_CLASSES)
def test_event_classes__every_class__category_is_declared(events_class):

    # arrange
    declared = EventCategory.VALUES

    # act
    category = events_class.CATEGORY

    # assert
    assert category in declared
    assert category != EventCategory.OTHER
