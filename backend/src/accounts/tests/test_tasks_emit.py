from datetime import date

import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.models import UserVacation
from src.accounts.tasks import process_vacations
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
    create_test_owner,
    create_test_vacation,
)

pytestmark = pytest.mark.django_db


def test_process_vacations__start_date_reached__emit_system_activate(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=owner,
        substitutes=[substitute],
        start_date=date(2020, 1, 1),
        absence_status=AbsenceStatus.ACTIVE,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    send_delegation_mock = mocker.patch(
        'src.accounts.services.vacation.'
        'send_vacation_delegation_notification.delay',
    )

    # act
    process_vacations()

    # assert
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_ACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(type=ActorType.SYSTEM)
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=owner.id,
    )
    assert event.payload == {
        'target_email': owner.email,
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'start_date': '2020-01-01',
        'end_date': None,
        'delegated_tasks_count': 0,
        'is_update': True,
    }
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_process_vacations__end_date_passed__emit_system_deactivate(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=owner,
        substitutes=[substitute],
        end_date=date(2020, 1, 1),
        absence_status=AbsenceStatus.VACATION,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )

    # act
    process_vacations()

    # assert
    assert not UserVacation.objects.filter(user=owner).exists()
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.USER_VACATION_DEACTIVATE
    assert event.category == EventCategory.AUDIT
    assert event.account_id == account.id
    assert event.actor == Actor(type=ActorType.SYSTEM)
    assert event.object == EventObject(
        type=EventObjectType.USER,
        id=owner.id,
    )
    assert event.payload == {'target_email': owner.email}
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_process_vacations__end_date_ahead__no_event(
    mocker,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(account=account)
    create_test_vacation(
        user=owner,
        substitutes=[substitute],
        end_date=date(2099, 12, 31),
        absence_status=AbsenceStatus.VACATION,
    )
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )

    # act
    process_vacations()

    # assert
    assert UserVacation.objects.filter(user=owner).exists()
    assert fake_stream.events == []
    send_user_updated_mock.assert_not_called()
