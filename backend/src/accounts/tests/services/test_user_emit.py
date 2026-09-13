import pytest

from src.accounts.enums import AbsenceStatus, UserStatus
from src.accounts.messages import MSG_A_0055
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
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
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_vacation,
)

pytestmark = pytest.mark.django_db


def test_partial_update__no_request_user__emit_system_password_set(
    mocker,
    identify_mock,
    fake_stream,
):

    """ Nobody is behind a service without a user, so a password it
        sends is set for the person, never changed by them. """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    service = UserService(
        account=account,
        instance=target,
    )

    # act
    service.partial_update(raw_password='new strong password')

    # assert
    assert len(fake_stream.events) == 2
    event_object = EventObject(
        type=EventObjectType.USER,
        id=target.id,
    )
    update_event = fake_stream.events[0][1]
    assert update_event.type == EventName.USER_UPDATE
    assert update_event.category == EventCategory.AUDIT
    assert update_event.account_id == account.id
    assert update_event.actor == Actor(type=ActorType.SYSTEM)
    assert update_event.object == event_object
    assert update_event.payload == {
        'target_email': target.email,
        'changed_fields': ['password'],
    }
    password_event = fake_stream.events[1][1]
    assert password_event.type == EventName.USER_PASSWORD_SET
    assert password_event.category == EventCategory.AUDIT
    assert password_event.account_id == account.id
    assert password_event.actor == Actor(type=ActorType.SYSTEM)
    assert password_event.object == event_object
    assert password_event.payload == {'target_email': target.email}
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_partial_update__group_instances__emit_group_ids(
    mocker,
    identify_mock,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    group = create_test_group(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    service.partial_update(user_groups=[group])

    # assert
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
        'added_groups_ids': [group.id],
        'removed_groups_ids': [],
    }
    identify_mock.assert_called_once_with(target)
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_partial_update__service_exception__no_event(
    mocker,
    identify_mock,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.user.send_user_updated_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    with pytest.raises(UserServiceException) as ex:
        service.partial_update(
            first_name='New',
            manager=target,
        )

    # assert
    assert ex.value.message == str(MSG_A_0055)
    assert fake_stream.events == []
    identify_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()


def test_deactivate__absent_user__emit_vacation_deactivate_by_request_user(
    mocker,
    identify_mock,
    group_mock,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    target = create_test_admin(account=account)
    substitute = create_test_not_admin(account=account)
    create_test_vacation(
        user=target,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    identify_users_mock = mocker.patch(
        'src.accounts.services.account.identify_users.delay',
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_user_deactivated_mock = mocker.patch(
        'src.notifications.tasks.send_user_deactivated_notification.delay',
    )
    send_user_deleted_mock = mocker.patch(
        'src.notifications.tasks.send_user_deleted_notification.delay',
    )
    service = UserService(
        user=owner,
        instance=target,
    )

    # act
    service.deactivate()

    # assert
    target.refresh_from_db()
    assert target.status == UserStatus.INACTIVE
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
    vacation_event = fake_stream.events[0][1]
    assert vacation_event.type == EventName.USER_VACATION_DEACTIVATE
    assert vacation_event.category == EventCategory.AUDIT
    assert vacation_event.account_id == account.id
    assert vacation_event.actor == actor
    assert vacation_event.object == event_object
    assert vacation_event.payload == {'target_email': target.email}
    deactivate_event = fake_stream.events[1][1]
    assert deactivate_event.type == EventName.USER_DEACTIVATE
    assert deactivate_event.account_id == account.id
    assert deactivate_event.actor == actor
    assert deactivate_event.object == event_object
    assert deactivate_event.payload == {
        'target_email': target.email,
        'status_before': UserStatus.ACTIVE,
    }
    identify_mock.assert_called_once_with(target)
    group_mock.assert_called_once_with(
        user=target,
        account=account,
    )
    identify_users_mock.assert_called_once_with(
        user_ids=(owner.id, substitute.id),
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
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
