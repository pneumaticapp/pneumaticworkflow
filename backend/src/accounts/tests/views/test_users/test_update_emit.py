import pytest

from src.accounts.messages import MSG_A_0055
from src.authentication.enums import AuthTokenType
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.payment.stripe.service import StripeService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_update__name_changed__emit_user_update(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        first_name='Old',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(
        owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.9',
    )

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New', 'last_name': target.last_name},
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
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'changed_fields': ['first_name'],
    }
    assert event.ip == '10.10.0.9'
    assert event.user_agent == 'Chrome/141'
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__same_values__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    """ The form sends every field on every save: an update that
        changes nothing is not an action worth a record. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    group = create_test_group(
        account=account,
        users=[target],
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={
            'first_name': target.first_name,
            'last_name': target.last_name,
            'phone': target.phone,
            'is_admin': False,
            'groups': [group.id],
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert fake_stream.events == []
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__email_changed__emit_previous_email(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        email='old@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'email': 'new@test.test'},
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
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': 'new@test.test',
        'changed_fields': ['email'],
        'previous_email': 'old@test.test',
    }
    assert event.pii == (
        'actor.email',
        'ip',
        'user_agent',
        'payload.target_email',
        'payload.previous_email',
    )
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__groups_changed__emit_added_and_removed_group_ids(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    old_group = create_test_group(
        account=account,
        name='old',
        users=[target],
    )
    new_group_1 = create_test_group(
        account=account,
        name='new 1',
    )
    new_group_2 = create_test_group(
        account=account,
        name='new 2',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'groups': [new_group_2.id, new_group_1.id]},
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
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'changed_fields': ['groups'],
        'added_groups_ids': [new_group_1.id, new_group_2.id],
        'removed_groups_ids': [old_group.id],
    }
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__manager_changed__emit_manager_id(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    manager = create_test_not_admin(
        account=account,
        email='manager@test.test',
    )
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'manager_id': manager.id},
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
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'changed_fields': ['manager'],
        'manager_id': manager.id,
    }
    identify_mock.assert_called_once_with(target)
    assert send_user_updated_mock.call_count == 2
    send_user_updated_mock.assert_has_calls([
        mocker.call(
            logging=False,
            account_id=account.id,
            user_data=mocker.ANY,
        ),
        mocker.call(
            logging=account.log_api_requests,
            account_id=account.id,
            user_data=mocker.ANY,
        ),
    ])


def test_update__subordinates_changed__emit_subordinates(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    subordinate = create_test_not_admin(
        account=account,
        email='subordinate@test.test',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'subordinates_ids': [subordinate.id]},
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
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'changed_fields': ['subordinates'],
    }
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__admin_granted__emit_update_then_admin_toggle(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    """ A grant of admin made through the edit form must reach the
        alert that watches user.admin_toggle. """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'is_admin': True},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 2
    actor = Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    event_object = EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.category == EventCategory.AUDIT
    assert update_event.account_id == account.id
    assert update_event.actor == actor
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': target.email,
        'changed_fields': ['is_admin'],
    }
    toggle_event = fake_stream.events[1][1]
    assert toggle_event.type == EventName.USER_ADMIN_TOGGLE
    assert toggle_event.category == EventCategory.AUDIT
    assert toggle_event.account_id == account.id
    assert toggle_event.actor == actor
    assert toggle_event.object == event_object
    assert toggle_event.payload == {
        'is_admin': True,
        'target_email': target.email,
    }
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__password_set_by_admin__emit_update_then_password_set(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'password': 'new strong password'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 2
    actor = Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    event_object = EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.category == EventCategory.AUDIT
    assert update_event.account_id == account.id
    assert update_event.actor == actor
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': target.email,
        'changed_fields': ['password'],
    }
    password_event = fake_stream.events[1][1]
    assert password_event.type == EventName.USER_PASSWORD_SET
    assert password_event.category == EventCategory.AUDIT
    assert password_event.account_id == account.id
    assert password_event.actor == actor
    assert password_event.object == event_object
    assert password_event.payload == {'target_email': target.email}
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__admin_and_password__emit_three_events_in_order(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={
            'first_name': 'Changed',
            'is_admin': True,
            'password': 'new strong password',
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 3
    actor = Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    event_object = EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.account_id == account.id
    assert update_event.actor == actor
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': target.email,
        'changed_fields': ['first_name', 'is_admin', 'password'],
    }
    admin_event = fake_stream.events[1][1]
    assert admin_event.type == EventName.USER_ADMIN_TOGGLE
    assert admin_event.account_id == account.id
    assert admin_event.actor == actor
    assert admin_event.object == event_object
    assert admin_event.payload == {
        'is_admin': True,
        'target_email': target.email,
    }
    password_event = fake_stream.events[2][1]
    assert password_event.type == EventName.USER_PASSWORD_SET
    assert password_event.account_id == account.id
    assert password_event.actor == actor
    assert password_event.object == event_object
    assert password_event.payload == {'target_email': target.email}
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__owner_sets_own_password__emit_password_change(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    update_customer_mock = mocker.patch(
        'src.payment.stripe.service.StripeService.update_customer',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{owner.id}',
        data={'password': 'new strong password'},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 2
    actor = Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    event_object = EventObject(
        type=EventObjectType.USER,
        id=owner.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.account_id == account.id
    assert update_event.actor == actor
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': owner.email,
        'changed_fields': ['password'],
    }
    password_event = fake_stream.events[1][1]
    assert password_event.type == EventName.USER_PASSWORD_CHANGE
    assert password_event.category == EventCategory.AUDIT
    assert password_event.account_id == account.id
    assert password_event.actor == actor
    assert password_event.object == event_object
    assert password_event.payload == {}
    identify_mock.assert_called_once_with(owner)
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    update_customer_mock.assert_called_once_with()
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__api_key_auth__emit_api_key_actor(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(
        account=account,
        first_name='Old',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(
        owner,
        token_type=AuthTokenType.API,
    )

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New'},
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
        type=ActorType.API_KEY,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    assert event.payload == {
        'target_email': target.email,
        'changed_fields': ['first_name'],
    }
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_update__service_exception__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New', 'manager_id': target.id},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0055)
    assert response.data['details'] == {}
    assert fake_stream.events == []
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_update__validation_error__no_event(
    mocker,
    identify_mock,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.put(
        f'/accounts/users/{target.id}',
        data={'first_name': 'New', 'photo': 'invalid_url'},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == 'Enter a valid URL.'
    assert response.data['details']['name'] == 'photo'
    assert response.data['details']['reason'] == 'Enter a valid URL.'
    assert fake_stream.events == []
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
