import pytest

from src.accounts.messages import MSG_A_0046
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
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_put__name_changed__emit_user_update_on_self(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(
        account=account,
        last_name='Old',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(
        user,
        user_agent='Chrome/141',
        user_ip='10.10.0.10',
    )

    # act
    response = api_client.put(
        '/accounts/user',
        data={'first_name': user.first_name, 'last_name': 'New'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_UPDATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'target_email': user.email,
        'changed_fields': ['last_name'],
    }
    assert event.ip == '10.10.0.10'
    assert event.user_agent == 'Chrome/141'
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__password_sent__emit_update_then_password_change(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'password': 'new strong password'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 2
    actor = Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    event_object = EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.category == EventCategory.AUDIT
    assert update_event.account_id == account.id
    assert update_event.actor == actor
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': user.email,
        'changed_fields': ['password'],
    }
    password_event = fake_stream.events[1][1]
    assert password_event.type == EventName.USER_PASSWORD_CHANGE
    assert password_event.category == EventCategory.AUDIT
    assert password_event.account_id == account.id
    assert password_event.actor == actor
    assert password_event.object == event_object
    assert password_event.payload == {}
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__admin_revokes_own_admin__emit_update_then_admin_toggle(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'is_admin': False},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 2
    actor = Actor(
        type=ActorType.USER,
        id=user.id,
        email=user.email,
    )
    event_object = EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.account_id == account.id
    assert update_event.actor == actor
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': user.email,
        'changed_fields': ['is_admin'],
    }
    toggle_event = fake_stream.events[1][1]
    assert toggle_event.type == EventName.USER_ADMIN_TOGGLE
    assert toggle_event.category == EventCategory.AUDIT
    assert toggle_event.account_id == account.id
    assert toggle_event.actor == actor
    assert toggle_event.object == event_object
    assert toggle_event.payload == {
        'is_admin': False,
        'target_email': user.email,
    }
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__same_values__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'language': user.language,
            'timezone': user.timezone,
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    identify_mock.assert_called_once_with(user)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_put__escalate_privileges__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={'is_admin': True},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0046)
    assert response.data['details']['name'] == 'is_admin'
    assert response.data['details']['reason'] == str(MSG_A_0046)
    assert fake_stream.events == []
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_put__blank_photo_over_null__not_emit(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    """ A profile without a photo stores NULL, the client sends it back
        as an empty string: the same absence, not an edit. """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account, photo=None)
    mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.put(
        '/accounts/user',
        data={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'photo': '',
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
