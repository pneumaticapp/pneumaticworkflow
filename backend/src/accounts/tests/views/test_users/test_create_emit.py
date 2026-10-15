import pytest

from src.accounts.services.exceptions import UserServiceException
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__admin_adds_user__audit_user_created(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    created = create_test_not_admin(
        account=account,
        email='new@test.test',
    )
    create_mock = mocker.patch.object(
        UserService,
        attribute='create',
        return_value=created,
    )
    user_created_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_created',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        {'email': 'new@test.test', 'is_admin': False},
    )

    # assert
    assert response.status_code == 200
    user_created_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        target=created,
    )
    create_mock.assert_called_once_with(
        account=account,
        email='new@test.test',
        is_admin=False,
    )


def test_create__not_admin__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    create_mock = mocker.patch.object(
        UserService,
        attribute='create',
    )
    user_created_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_created',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/accounts/users', {'email': 'x@test.test'})

    # assert
    assert response.status_code == 403
    user_created_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__service_exception__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_mock = mocker.patch.object(
        UserService,
        attribute='create',
        side_effect=UserServiceException(message='Service error'),
    )
    user_created_mock = mocker.patch(
        'src.accounts.views.users.AuditEventService.user_created',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        '/accounts/users',
        {'email': 'new@test.test', 'is_admin': False},
    )

    # assert
    assert response.status_code == 400
    assert response.data == {
        'code': ErrorCode.VALIDATION_ERROR,
        'message': 'Service error',
        'details': {},
    }
    user_created_mock.assert_not_called()
    create_mock.assert_called_once_with(
        account=account,
        email='new@test.test',
        is_admin=False,
    )
