import pytest
from django.contrib.auth import get_user_model
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.utils.validation import ErrorCode
from src.accounts.messages import MSG_A_0050
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_set_reports__ok(api_client, mocker):
    # arrange
    account = create_test_account()
    team_member = create_test_not_admin(account=account)
    report = create_test_not_admin(account=account, email='r@test.test')

    user_service_init_mock = mocker.patch.object(
        UserService,
        attribute='__init__',
        return_value=None,
    )
    set_reports_mock = mocker.patch(
        'src.accounts.views.user.UserService.set_reports',
        return_value=team_member,
    )
    api_client.token_authenticate(team_member)

    # act
    response = api_client.post(
        '/accounts/user/set-reports',
        data={'report_ids': [report.id]},
    )

    # assert
    assert response.status_code == 200
    user_service_init_mock.assert_called_once_with(
        user=team_member,
        instance=team_member,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    set_reports_mock.assert_called_once()


def test_set_reports__circular_hierarchy__validation_error(api_client, mocker):
    # arrange
    account = create_test_account()
    user_a = create_test_not_admin(account=account, email='a@test.test')
    user_b = create_test_not_admin(account=account, email='b@test.test')

    # user_a is manager of user_b
    user_b.manager = user_a
    user_b.save()

    api_client.token_authenticate(user_b)
    set_reports_mock = mocker.patch(
        'src.accounts.views.user.UserService.set_reports',
    )

    # act
    # user_b attempts to become manager of user_a (circular!)
    response = api_client.post(
        '/accounts/user/set-reports',
        data={'report_ids': [user_a.id]},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0050
    set_reports_mock.assert_not_called()


def test_set_reports__guest__permission_denied(api_client, mocker):
    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    report = create_test_not_admin(account=account, email='r@test.test')
    workflow = create_test_workflow(
        owner,
        tasks_count=1,
    )
    task = workflow.tasks.first()
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    set_reports_mock = mocker.patch(
        'src.accounts.views.user.UserService.set_reports',
    )

    # act
    response = api_client.post(
        '/accounts/user/set-reports',
        data={'report_ids': [report.id]},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403
    set_reports_mock.assert_not_called()
