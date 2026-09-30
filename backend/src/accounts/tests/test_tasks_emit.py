from datetime import date

import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.models import UserVacation
from src.accounts.tasks import process_vacations
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_vacation,
)

pytestmark = pytest.mark.django_db


def test_process_vacations__start_date_reached__audit_no_user(mocker):

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
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.'
        'vacation_activated',
    )

    # act
    process_vacations()

    # assert
    vacation_activated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=owner,
        substitute_user_ids=[substitute.id],
        absence_status=AbsenceStatus.VACATION,
        start_date=date(2020, 1, 1),
        end_date=None,
        delegated_tasks_count=0,
        is_update=True,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_process_vacations__end_date_passed__audit_no_user(mocker):

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
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.'
        'vacation_deactivated',
    )

    # act
    process_vacations()

    # assert
    assert not UserVacation.objects.filter(user=owner).exists()
    vacation_deactivated_mock.assert_called_once_with(
        user=None,
        auth_type=AuthTokenType.USER,
        target=owner,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_process_vacations__end_date_ahead__audit_not_called(mocker):

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
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.'
        'vacation_deactivated',
    )

    # act
    process_vacations()

    # assert
    assert UserVacation.objects.filter(user=owner).exists()
    vacation_deactivated_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
