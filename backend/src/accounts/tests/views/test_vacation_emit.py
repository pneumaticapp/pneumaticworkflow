from datetime import date

import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.messages import MSG_A_0049, MSG_A_0052
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
    create_test_vacation,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_user_activate_vacation__self__emit_actor_is_the_user(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    api_client.token_authenticate(
        user,
        user_agent='Chrome/141',
        user_ip='10.10.0.15',
    )

    # act
    response = api_client.post(
        '/accounts/user/activate-vacation',
        data={'substitute_user_ids': [substitute.id]},
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
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
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': None,
        'end_date': None,
        'delegated_tasks_count': 0,
        'is_update': False,
    }
    assert event.ip == '10.10.0.15'
    assert event.user_agent == 'Chrome/141'
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_users_activate_vacation__admin_for_user__emit_actor_is_admin(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{user.id}/activate-vacation',
        data={
            'substitute_user_ids': [substitute.id],
            'absence_status': AbsenceStatus.SICK_LEAVE,
            'vacation_start_date': '2026-09-01',
            'vacation_end_date': '2026-09-20',
        },
        format='json',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {
        'target_email': user.email,
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.SICK_LEAVE,
        'start_date': '2026-09-01',
        'end_date': '2026-09-20',
        'delegated_tasks_count': 0,
        'is_update': False,
    }
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_user_activate_vacation__self_as_substitute__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/user/activate-vacation',
        data={'substitute_user_ids': [user.id]},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0049)
    assert response.data['details']['name'] == 'substitute_user_ids'
    assert response.data['details']['reason'] == str(MSG_A_0049)
    assert fake_stream.events == []
    send_user_updated_mock.assert_not_called()
    send_delegation_mock.assert_not_called()


def test_users_deactivate_vacation__admin_for_user__emit_actor_is_admin(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=user,
        substitutes=[substitute],
        absence_status=AbsenceStatus.VACATION,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{user.id}/deactivate-vacation',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_DEACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=user.id,
    )
    assert event.payload == {'target_email': user.email}
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_user_deactivate_vacation__self__emit_actor_is_the_user(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=user,
        substitutes=[substitute],
        start_date=date(2099, 1, 1),
        absence_status=AbsenceStatus.ACTIVE,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/accounts/user/deactivate-vacation')

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_DEACTIVATE
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
    assert event.payload == {'target_email': user.email}
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_user_deactivate_vacation__no_vacation__no_event(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/accounts/user/deactivate-vacation')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0052)
    assert response.data['details'] == {}
    assert fake_stream.events == []
    send_user_updated_mock.assert_not_called()
