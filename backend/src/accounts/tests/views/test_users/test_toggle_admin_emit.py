import pytest

from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
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
    emit_mock = mocker.patch('src.logs.events.mixins.emit')

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
    )

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        EventName.USER_ADMIN_TOGGLE,
        account_id=owner.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={'is_admin': True, 'target_email': target.email},
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
    emit_mock = mocker.patch('src.logs.events.mixins.emit')

    # act
    response = api_client.post(
        f'/accounts/users/{target.id}/toggle-admin',
    )

    # assert
    assert response.status_code == 204
    emit_mock.assert_called_once_with(
        EventName.USER_ADMIN_TOGGLE,
        account_id=owner.account_id,
        actor=Actor(
            type=ActorType.USER,
            id=owner.id,
            email=owner.email,
        ),
        event_object=EventObject(type=EventObjectType.USER, id=target.id),
        payload={'is_admin': False, 'target_email': target.email},
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
    assert event.type == EventName.USER_ADMIN_TOGGLE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == owner.account_id
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
        'is_admin': True,
        'target_email': target.email,
    }
    assert event.ip == '10.10.0.7'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-toggle-1'
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=owner.account_id,
        user_data=mocker.ANY,
    )
