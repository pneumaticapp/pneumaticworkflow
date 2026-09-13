import pytest

from src.accounts.enums import UserStatus
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_destroy__users_endpoint__emit_user_deactivate(
    mocker,
    identify_mock,
    group_mock,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(owner)
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    emit_mock = mocker.patch('src.logs.events.mixins.emit')

    # act
    response = api_client.delete(f'/accounts/users/{target.id}')

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        EventName.USER_DEACTIVATE,
        account_id=account.id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={
            'target_email': target.email,
            'status_before': UserStatus.ACTIVE,
        },
    )
    identify_mock.assert_called_once_with(target)
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))
    group_mock.assert_called_once_with(user=target, account=account)
    send_user_deactivated_mock.assert_called_once_with(
        user_id=target.id,
        user_email=target.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_destroy__service_emit__event_keeps_request_context(
    mocker,
    identify_mock,
    group_mock,
    api_client,
    fake_stream,
):

    """ The service has no request, so the address, the browser and
        the correlation id can only come from the context published
        by the middleware. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.8',
    )
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )

    # act
    response = api_client.delete(
        f'/accounts/users/{target.id}',
        HTTP_X_REQUEST_ID='audit-deactivate-1',
    )

    # assert
    assert response.status_code == 204
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_DEACTIVATE
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'status_before': UserStatus.ACTIVE,
    }
    assert event.ip == '10.10.0.8'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-deactivate-1'
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
    )
    identify_mock.assert_called_once_with(target)
    identify_users_mock.assert_called_once_with(user_ids=(owner.id,))
    group_mock.assert_called_once_with(user=target, account=account)
    send_user_deactivated_mock.assert_called_once_with(
        user_id=target.id,
        user_email=target.email,
        account_id=account.id,
        logo_lg=account.logo_lg,
    )
    send_user_deleted_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
