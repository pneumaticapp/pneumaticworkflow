from datetime import timedelta

import pytest

from src.accounts.enums import SourceType, UserType
from src.authentication.enums import AuthTokenType
from src.authentication.messages import MSG_AU_0016
from src.logs.events.schema import Actor, EventObject
from src.logs.events.emitter import NO_ACCOUNT
from src.logs.events.enums import (
    EventObjectType,
    LoginFailedReason,
    UserEvents,
)
from src.processes.tests.fixtures import (
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_signin__valid_credentials__emit_user_login(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN,
        account_id=user.account_id,
        actor=Actor(
            id=user.id,
            email=user.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(type=EventObjectType.USER, id=user.id),
        payload={'source': SourceType.EMAIL},
    )
    identify_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.EMAIL,
    )


def test_signin__valid_credentials__event_keeps_request_context(
    mocker,
    api_client,
    identify_mock,
    fake_stream,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
        HTTP_USER_AGENT='Chrome/141',
        HTTP_X_REAL_IP='10.10.0.21',
        HTTP_X_REQUEST_ID='audit-signin-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == UserEvents.LOGIN
    assert event.category == UserEvents.CATEGORY
    assert event.account_id == user.account_id
    assert event.actor == Actor(
        id=user.id,
        email=user.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'source': SourceType.EMAIL}
    assert event.ip == '10.10.0.21'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-signin-1'
    identify_mock.assert_called_once_with(user)
    users_logged_in_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        source=SourceType.EMAIL,
    )


def test_signin__wrong_password__emit_login_failed(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': 'YouShallNotPass',
        },
    )

    # assert
    assert response.status_code == 403
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN_FAILED,
        account_id=NO_ACCOUNT,
        event_object=EventObject(type=EventObjectType.USER),
        payload={
            'email': user.email,
            'reason': LoginFailedReason.BAD_CREDENTIALS,
        },
    )
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__wrong_password__event_keeps_request_context(
    mocker,
    api_client,
    identify_mock,
    fake_stream,
):

    """ A failed attempt is the event an alert on a brute force
        burst is built on: the address of the attempt has to be
        there even though nobody is signed in. """

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': 'YouShallNotPass',
        },
        HTTP_USER_AGENT='Chrome/141',
        HTTP_X_REAL_IP='10.10.0.22',
        HTTP_X_REQUEST_ID='audit-signin-2',
    )

    # assert
    assert response.status_code == 403
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == UserEvents.LOGIN_FAILED
    assert event.account_id == NO_ACCOUNT
    assert event.actor is None
    assert event.auth_type is None
    assert event.object == EventObject(type=EventObjectType.USER)
    assert event.payload == {
        'email': user.email,
        'reason': LoginFailedReason.BAD_CREDENTIALS,
    }
    assert event.ip == '10.10.0.22'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-signin-2'
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__unknown_email__emit_login_failed_with_same_reason(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': 'ghost@pneumatic.app',
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 403
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN_FAILED,
        account_id=NO_ACCOUNT,
        event_object=EventObject(type=EventObjectType.USER),
        payload={
            'email': 'ghost@pneumatic.app',
            'reason': LoginFailedReason.BAD_CREDENTIALS,
        },
    )
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__uppercase_email_with_spaces__emit_normalized_email(
    mocker,
    api_client,
    identify_mock,
):

    # arrange
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': '  OWNER@Pneumatic.APP  ',
            'password': 'YouShallNotPass',
        },
    )

    # assert
    assert response.status_code == 403
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN_FAILED,
        account_id=NO_ACCOUNT,
        event_object=EventObject(type=EventObjectType.USER),
        payload={
            'email': 'owner@pneumatic.app',
            'reason': LoginFailedReason.BAD_CREDENTIALS,
        },
    )
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__sso_required__emit_login_failed_sso_required(
    mocker,
    api_client,
    identify_mock,
    settings,
):

    # arrange
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'SSO_AUTH': True}
    user = create_test_admin()
    user.set_password('12345')
    user.save(update_fields=['password'])
    users_logged_in_mock = mocker.patch(
        'src.authentication.views.signin.'
        'AnalyticService.users_logged_in',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 400
    assert response.data[0] == MSG_AU_0016
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN_FAILED,
        account_id=NO_ACCOUNT,
        event_object=EventObject(type=EventObjectType.USER),
        payload={
            'email': user.email,
            'reason': LoginFailedReason.SSO_REQUIRED,
        },
    )
    identify_mock.assert_not_called()
    users_logged_in_mock.assert_not_called()


def test_signin__verification_timed_out__emit_login_failed_inactive(
    mocker,
    api_client,
    identify_mock,
    verification_check_true_mock,
):

    # arrange
    user = create_test_owner()
    user.set_password('12345')
    user.save(update_fields=['password'])
    account = user.account
    account.is_verified = False
    account.date_joined = user.date_joined - timedelta(weeks=3)
    account.save(update_fields=['is_verified', 'date_joined'])
    send_verification_mock = mocker.patch(
        'src.authentication.views.signin.'
        'send_verification_notification.delay',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        path='/auth/token/obtain',
        data={
            'username': user.email,
            'password': '12345',
        },
    )

    # assert
    assert response.status_code == 403
    emit_mock.assert_called_once_with(
        UserEvents.LOGIN_FAILED,
        account_id=NO_ACCOUNT,
        event_object=EventObject(type=EventObjectType.USER),
        payload={
            'email': user.email,
            'reason': LoginFailedReason.VERIFICATION_EXPIRED,
        },
    )
    identify_mock.assert_not_called()
    send_verification_mock.assert_called_once_with(
        user_id=user.id,
        user_email=user.email,
        account_id=user.account_id,
        user_first_name=user.first_name,
        token=mocker.ANY,
        logo_lg=account.logo_lg,
    )
