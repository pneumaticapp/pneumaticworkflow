import pytest

from src.authentication.enums import AuthTokenType
from src.logs.events.schema import Actor, EventObject
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_signout__user_token__emit_user_logout(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    token = api_client.token_authenticate(user)

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        EventName.USER_LOGOUT,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.USER, id=user.id),
        payload={'auth_type': AuthTokenType.USER},
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )
    expire_token_mock.assert_called_once_with(token)


def test_signout__user_token__event_keeps_request_context(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_owner()
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    token = api_client.token_authenticate(
        user,
        user_agent='Chrome/141',
        user_ip='10.10.0.24',
    )

    # act
    response = api_client.post(
        '/auth/signout',
        HTTP_X_REQUEST_ID='audit-signout-1',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_LOGOUT
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'auth_type': AuthTokenType.USER}
    assert event.ip == '10.10.0.24'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-signout-1'
    expire_token_mock.assert_called_once_with(token)


def test_signout__api_key__emit_user_logout_with_api_key_actor(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner()
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    api_client.token_authenticate(user, token_type=AuthTokenType.API)

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        EventName.USER_LOGOUT,
        account_id=user.account_id,
        actor=Actor(
            type=ActorType.API_KEY,
            id=user.id,
            email=user.email,
        ),
        event_object=EventObject(type=EventObjectType.USER, id=user.id),
        payload={'auth_type': AuthTokenType.API},
        workflow_id=None,
        task_id=None,
        request=mocker.ANY,
    )
    expire_token_mock.assert_not_called()


def test_signout__not_authenticated__no_event(
    mocker,
    api_client,
):

    # arrange
    expire_token_mock = mocker.patch(
        'src.authentication.tokens.'
        'PneumaticToken.expire_token',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post('/auth/signout')

    # assert
    assert response.status_code == 401
    emit_mock.assert_not_called()
    expire_token_mock.assert_not_called()
