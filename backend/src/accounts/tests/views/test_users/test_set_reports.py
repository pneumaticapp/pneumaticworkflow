import pytest
from django.contrib.auth import get_user_model
from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.utils.validation import ErrorCode
from src.accounts.messages import MSG_A_0049, MSG_A_0050
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_set_reports__ok(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    team_member = create_test_not_admin(account=account)
    report1 = create_test_not_admin(
        account=account,
        email='report1@test.test',
    )
    report2 = create_test_not_admin(
        account=account,
        email='report2@test.test',
    )

    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    set_reports_mock = mocker.patch(
        'src.accounts.views.users.UserService.set_reports',
        return_value=team_member,
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/set-reports',
        data={'report_ids': [report1.id, report2.id]},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=owner,
        instance=team_member,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    set_reports_mock.assert_called_once()
    kwargs = set_reports_mock.call_args[1]
    reports = kwargs['reports']
    assert len(reports) == 2
    assert report1 in reports
    assert report2 in reports


def test_set_reports__circular_hierarchy__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user_a = create_test_not_admin(account=account, email='a@test.test')
    user_b = create_test_not_admin(account=account, email='b@test.test')

    # user_a is manager of user_b
    user_b.manager = user_a
    user_b.save()

    api_client.token_authenticate(owner)
    set_reports_mock = mocker.patch(
        'src.accounts.views.users.UserService.set_reports',
    )

    # act
    # user_b attempts to become manager of user_a (circular!)
    response = api_client.post(
        f'/accounts/users/{user_b.id}/set-reports',
        data={'report_ids': [user_a.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0050
    set_reports_mock.assert_not_called()


def test_set_reports__self_assignment__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    team_member = create_test_not_admin(account=account)
    api_client.token_authenticate(owner)
    set_reports_mock = mocker.patch(
        'src.accounts.views.users.UserService.set_reports',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/set-reports',
        data={'report_ids': [team_member.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0049
    set_reports_mock.assert_not_called()


def test_set_reports__other_account_user__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    other_account = create_test_account()
    owner = create_test_owner(account=account)
    team_member = create_test_not_admin(account=account)
    other_user = create_test_not_admin(
        account=other_account,
        email='other@test.test',
    )
    api_client.token_authenticate(owner)
    set_reports_mock = mocker.patch(
        'src.accounts.views.users.UserService.set_reports',
    )

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/set-reports',
        data={'report_ids': [other_user.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    set_reports_mock.assert_not_called()


def test_set_reports__service_exception__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    team_member = create_test_not_admin(account=account)
    report = create_test_not_admin(account=account, email='report@test.test')

    api_client.token_authenticate(owner)

    mocker.patch(
        'src.accounts.views.users.UserService.set_reports',
        side_effect=UserServiceException('Some error'),
    )

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/set-reports',
        data={'report_ids': [report.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == 'Some error'


def test_set_reports__not_admin__permission_denied(api_client, mocker):
    # arrange
    account = create_test_account()
    team_member = create_test_not_admin(account=account)
    report = create_test_not_admin(account=account, email='report@test.test')

    set_reports_mock = mocker.patch(
        'src.accounts.views.users.UserService.set_reports',
    )
    api_client.token_authenticate(team_member)

    # act
    response = api_client.post(
        f'/accounts/users/{team_member.id}/set-reports',
        data={'report_ids': [report.id]},
    )

    # assert
    assert response.status_code == 403
    set_reports_mock.assert_not_called()
