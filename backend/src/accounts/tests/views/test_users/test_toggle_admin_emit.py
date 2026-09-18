import pytest

from src.accounts.enums import UserType
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    EventObjectType,
    UserEvents,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_toggle_admin__grant__emit_admin_toggle_with_true(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    api_client.token_authenticate(owner)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
    )

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        UserEvents.ADMIN_TOGGLE,
        account_id=owner.account_id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={'is_admin': True, 'target_email': target.email},
        workflow_id=None,
        task_id=None,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )


def test_toggle_admin__revoke__emit_admin_toggle_with_false(
    mocker,
    identify_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(owner)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
    )

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        UserEvents.ADMIN_TOGGLE,
        account_id=owner.account_id,
        actor=Actor(
            id=owner.id,
            email=owner.email,
            user_type=UserType.USER,
        ),
        auth_type=AuthTokenType.USER,
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={'is_admin': False, 'target_email': target.email},
        workflow_id=None,
        task_id=None,
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )


def test_toggle_admin__api_request__event_keeps_request_context(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    """ An emit mock cannot compare a DRF request, so the address,
        the browser and the correlation id are checked on the stream
        the pipeline really writes to. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.7',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
        HTTP_X_REQUEST_ID='audit-toggle-1',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == UserEvents.ADMIN_TOGGLE
    assert event.category == UserEvents.CATEGORY
    assert event.account_id == owner.account_id
    assert event.actor == Actor(
        id=owner.id,
        email=owner.email,
        user_type=UserType.USER,
    )
    assert event.auth_type == AuthTokenType.USER
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'is_admin': True,
        'target_email': target.email,
    }
    assert event.ip == '10.10.0.7'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-toggle-1'
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )


def test_toggle_admin__not_admin__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    target = create_test_not_admin(
        account=account,
        email='target@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(f'/accounts/users/{target.id}/toggle-admin')

    # assert
    assert response.status_code == 403
    target.refresh_from_db()
    assert target.is_admin is False
    assert fake_stream.events == []
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_toggle_admin__user_of_another_account__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    other_account = create_test_account(name='Other')
    create_test_owner(
        account=other_account,
        email='other_owner@test.test',
    )
    target = create_test_not_admin(
        account=other_account,
        email='target@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/accounts/users/{target.id}/toggle-admin')

    # assert
    assert response.status_code == 404
    target.refresh_from_db()
    assert target.is_admin is False
    assert fake_stream.events == []
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
