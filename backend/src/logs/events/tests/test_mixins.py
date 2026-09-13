from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.logs.events.tests.fakes import FakeEmittingService


def test_event_actor__no_user__system():

    # arrange
    service = FakeEmittingService()

    # act
    actor = service._event_actor()

    # assert
    assert actor == Actor(type=ActorType.SYSTEM)


def test_event_actor__user_with_api_key__api_key_actor(mocker):

    # arrange
    user = mocker.Mock(id=5, email='ann@test.test')
    service = FakeEmittingService(user=user, auth_type=AuthTokenType.API)

    # act
    actor = service._event_actor()

    # assert
    assert actor == Actor(
        type=ActorType.API_KEY,
        id=5,
        email='ann@test.test',
    )


def test_publish__service_actor__emit_called_with_it(mocker):

    # arrange
    user = mocker.Mock(id=5, email='ann@test.test')
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = FakeEmittingService(user=user)

    # act
    service._publish(
        EventName.GROUP_CREATE,
        account_id=3,
        object_type=EventObjectType.GROUP,
        object_id=9,
        payload={'name': 'Support'},
        workflow_id=None,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.GROUP_CREATE,
        account_id=3,
        actor=Actor(type=ActorType.USER, id=5, email='ann@test.test'),
        event_object=EventObject(type=EventObjectType.GROUP, id=9),
        payload={'name': 'Support'},
        workflow_id=None,
    )


def test_publish__given_actor__wins_over_the_service_user(mocker):

    # arrange
    user = mocker.Mock(id=5, email='ann@test.test')
    emit_mock = mocker.patch('src.logs.events.mixins.emit')
    service = FakeEmittingService(user=user)
    invited = Actor(type=ActorType.USER, id=8, email='bob@test.test')

    # act
    service._publish(
        EventName.INVITE_ACCEPT,
        account_id=3,
        object_type=EventObjectType.INVITE,
        object_id='11',
        actor=invited,
    )

    # assert
    emit_mock.assert_called_once_with(
        EventName.INVITE_ACCEPT,
        account_id=3,
        actor=invited,
        event_object=EventObject(type=EventObjectType.INVITE, id='11'),
        payload=None,
    )
