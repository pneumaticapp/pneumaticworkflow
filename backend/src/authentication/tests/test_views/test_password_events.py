import pytest

from src.accounts.tokens import ResetPasswordToken
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import create_test_user

pytestmark = pytest.mark.django_db


def test_reset_password__known_address__emit_reset_request(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_user()
    reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    inc_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        {'email': user.email},
        HTTP_X_REAL_IP='10.10.0.3',
        HTTP_USER_AGENT='Safari/18',
        HTTP_X_REQUEST_ID='audit-reset-1',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_PASSWORD_RESET_REQUEST
    assert event.category == EventCategory.AUDIT
    assert event.account_id == user.account_id
    assert event.actor == Actor(type=ActorType.GUEST)
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {'target_email': user.email}
    assert event.ip == '10.10.0.3'
    assert event.user_agent == 'Safari/18'
    assert event.request_id == 'audit-reset-1'
    reset_exists_mock.assert_called_once()
    inc_counter_mock.assert_called_once()
    send_reset_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        logo_lg=user.account.logo_lg,
        logging=user.account.log_api_requests,
        account_id=user.account_id,
    )


def test_reset_password__unknown_address__no_event(
    mocker,
    api_client,
    fake_stream,
):

    """ No e-mail goes out for an address nobody has, so nothing
        happened in any account. """

    # arrange
    reset_exists_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.anonymous_user_reset_exists',
        return_value=False,
    )
    inc_counter_mock = mocker.patch(
        'src.authentication.views.password.'
        'ResetPasswordViewSet.inc_anonymous_user_reset_counter',
    )
    send_reset_mock = mocker.patch(
        'src.authentication.views.password.'
        'send_reset_password_notification.delay',
    )

    # act
    response = api_client.post(
        '/auth/reset-password',
        {'email': 'nobody@test.test'},
    )

    # assert
    assert response.status_code == 204
    assert fake_stream.events == []
    reset_exists_mock.assert_called_once()
    inc_counter_mock.assert_called_once()
    send_reset_mock.assert_not_called()


def test_confirm__valid_token__emit_password_reset(
    mocker,
    api_client,
    expire_tokens_mock,
    fake_stream,
):

    # arrange
    user = create_test_user()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    data = {
        'new_password': 'new-pass-1',
        'confirm_new_password': 'new-pass-1',
        'token': str(ResetPasswordToken.for_user(user)),
    }

    # act
    response = api_client.post(
        '/auth/reset-password/confirm',
        data,
        HTTP_X_REAL_IP='10.10.0.4',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_PASSWORD_RESET
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {}
    assert event.ip == '10.10.0.4'
    change_password_mock.assert_called_once_with(password='new-pass-1')
    expire_tokens_mock.assert_called_once_with(user)


def test_change_password__authenticated__emit_password_change(
    mocker,
    api_client,
    expire_tokens_mock,
    fake_stream,
):

    # arrange
    user = create_test_user()
    user.set_password('12345')
    user.save()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    api_client.token_authenticate(
        user,
        user_agent='Chrome/141',
        user_ip='10.10.0.5',
    )

    # act
    response = api_client.post(
        '/auth/change-password',
        data={
            'old_password': '12345',
            'new_password': '54321',
            'confirm_new_password': '54321',
        },
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_PASSWORD_CHANGE
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(type=EventObjectType.USER, id=user.id)
    assert event.payload == {}
    assert event.ip == '10.10.0.5'
    assert event.user_agent == 'Chrome/141'
    change_password_mock.assert_called_once_with(password='54321')
    expire_tokens_mock.assert_called_once_with(user)


def test_change_password__wrong_old_password__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    user = create_test_user()
    user.set_password('12345')
    user.save()
    change_password_mock = mocker.patch(
        'src.accounts.services.user.UserService.change_password',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/auth/change-password',
        data={
            'old_password': 'wrong',
            'new_password': '54321',
            'confirm_new_password': '54321',
        },
    )

    # assert
    assert response.status_code == 400
    assert fake_stream.events == []
    change_password_mock.assert_not_called()
