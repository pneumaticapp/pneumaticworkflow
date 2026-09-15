import pytest

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.schema import Actor, EventObject
from src.logs.events.enums import (
    EventObjectType,
    UserEvents,
)
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_superuser_token__ok__emit_user_login_as(
    mocker,
    api_client,
):

    # arrange
    superuser = create_test_owner(email='superuser@pneumatic.app')
    superuser.is_superuser = True
    superuser.save(update_fields=['is_superuser'])
    target_user = create_test_owner(email='client@pneumatic.app')
    get_superuser_auth_token_mock = mocker.patch(
        'src.authentication.views.signin.AuthService.'
        'get_superuser_auth_token',
        return_value='NeverGonnaGiveYouUpNeverGonnaLet',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    api_client.token_authenticate(superuser)

    # act
    response = api_client.post(
        path='/auth/superuser/token',
        data={'email': target_user.email},
    )

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN_AS,
        account_id=target_user.account_id,
        actor=Actor(
            id=superuser.id,
            email=superuser.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(
            type=EventObjectType.USER,
            id=target_user.id,
        ),
        payload={'target_email': target_user.email},
        workflow_id=None,
        task_id=None,
    )
    get_superuser_auth_token_mock.assert_called_once_with(target_user)


def test_superuser_token__ok__event_keeps_request_context(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    superuser = create_test_owner(email='superuser@pneumatic.app')
    superuser.is_superuser = True
    superuser.save(update_fields=['is_superuser'])
    target_user = create_test_owner(email='client@pneumatic.app')
    get_superuser_auth_token_mock = mocker.patch(
        'src.authentication.views.signin.AuthService.'
        'get_superuser_auth_token',
        return_value='NeverGonnaGiveYouUpNeverGonnaLet',
    )
    api_client.token_authenticate(
        superuser,
        user_agent='Chrome/141',
        user_ip='10.10.0.23',
    )

    # act
    response = api_client.post(
        path='/auth/superuser/token',
        data={'email': target_user.email},
        HTTP_X_REQUEST_ID='audit-login-as-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == UserEvents.LOGIN_AS
    assert event.account_id == target_user.account_id
    assert event.actor == Actor(
        id=superuser.id,
        email=superuser.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target_user.id,
    )
    assert event.payload == {'target_email': target_user.email}
    assert event.ip == '10.10.0.23'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-login-as-1'
    get_superuser_auth_token_mock.assert_called_once_with(target_user)


def test_superuser_token__not_superuser__no_event(
    mocker,
    api_client,
):

    # arrange
    user = create_test_owner(email='regular@pneumatic.app')
    target_user = create_test_owner(email='client@pneumatic.app')
    get_superuser_auth_token_mock = mocker.patch(
        'src.authentication.views.signin.AuthService.'
        'get_superuser_auth_token',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/auth/superuser/token',
        data={'email': target_user.email},
    )

    # assert
    assert response.status_code == 403
    emit_mock.assert_not_called()
    get_superuser_auth_token_mock.assert_not_called()
