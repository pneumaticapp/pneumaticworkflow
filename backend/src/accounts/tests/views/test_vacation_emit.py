from datetime import date

import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.messages import MSG_A_0049, MSG_A_0052
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_vacation,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_user_activate_vacation__self__audit_user_is_the_target(
    mocker,
    api_client,
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
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/user/activate-vacation',
        data={'substitute_user_ids': [substitute.id]},
        format='json',
    )

    # assert
    assert response.status_code == 200
    vacation_activated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.VACATION,
        start_date=None,
        end_date=None,
        delegated_tasks_count=0,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute]
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_users_activate_vacation__admin_for_user__audit_user_is_admin(
    mocker,
    api_client,
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
    captured_substitutes = []
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
        side_effect=lambda **kwargs: captured_substitutes.append(
            kwargs['substitute_users'],
        ),
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
    vacation_activated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=user,
        substitute_users=captured_substitutes[0],
        absence_status=AbsenceStatus.SICK_LEAVE,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 20),
        delegated_tasks_count=0,
        is_update=False,
    )
    assert list(captured_substitutes[0].order_by('id')) == [substitute]
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )
    send_delegation_mock.assert_not_called()


def test_user_activate_vacation__self_as_substitute__audit_not_called(
    mocker,
    api_client,
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
    vacation_activated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.vacation_activated',
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
    vacation_activated_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
    send_delegation_mock.assert_not_called()


def test_users_deactivate_vacation__admin_for_user__audit_user_is_admin(
    mocker,
    api_client,
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
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.'
        'vacation_deactivated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{user.id}/deactivate-vacation',
    )

    # assert
    assert response.status_code == 200
    vacation_deactivated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=user,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_user_deactivate_vacation__self__audit_user_is_the_target(
    mocker,
    api_client,
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
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.'
        'vacation_deactivated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/accounts/user/deactivate-vacation')

    # assert
    assert response.status_code == 200
    vacation_deactivated_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        target=user,
    )
    send_user_updated_mock.assert_called_once_with(
        logging=account.log_api_requests,
        account_id=account.id,
        user_data=mocker.ANY,
    )


def test_user_deactivate_vacation__no_vacation__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    send_user_updated_mock = mocker.patch(
        'src.accounts.services.vacation.send_user_updated_notification.delay',
    )
    vacation_deactivated_mock = mocker.patch(
        'src.accounts.services.vacation.AuditEventService.'
        'vacation_deactivated',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/accounts/user/deactivate-vacation')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == str(MSG_A_0052)
    assert response.data['details'] == {}
    vacation_deactivated_mock.assert_not_called()
    send_user_updated_mock.assert_not_called()
