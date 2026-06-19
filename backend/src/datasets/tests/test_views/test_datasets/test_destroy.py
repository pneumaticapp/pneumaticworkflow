import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.authentication.enums import AuthTokenType
from src.datasets.exceptions import DataSetServiceException
from src.datasets.services.dataset import DataSetService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_destroy__unauthenticated__unauthorized(api_client):

    """Unauthenticated user — 401"""

    # arrange
    account = create_test_account()
    dataset = create_test_dataset(account=account)

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 401


def test_destroy__expired_subscription__permission_denied(api_client):

    """Expired subscription — 403"""

    # arrange

    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_destroy__billing_plan__permission_denied(api_client):

    """Billing plan restriction — 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_destroy__users_overlimited__permission_denied(api_client):

    """Users overlimited — 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    user = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='extra@pneumatic.app',
    )
    account.active_users = 2
    account.save()
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_destroy__non_admin__permission_denied(api_client):

    """Non-admin/non-owner user — 403"""

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 403


def test_destroy__not_found__not_found(api_client):

    """Non-existent dataset id — 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    non_existent_id = 999999

    # act
    response = api_client.delete(f'/datasets/{non_existent_id}')

    # assert
    assert response.status_code == 404


def test_destroy__another_account__not_found(api_client):

    """Dataset belonging to another account — 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)

    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account)

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 404


def test_destroy__service_exception__validation_error(mocker, api_client):

    """`DataSetServiceException` raised — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)
    error_message = 'Cannot delete dataset'
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    delete_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.delete',
        side_effect=DataSetServiceException(
            message=error_message,
        ),
    )

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        instance=dataset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    delete_mock.assert_called_once_with()


def test_destroy__ok(mocker, api_client):

    """Valid request — 200"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    delete_mock = mocker.patch(
        'src.datasets.services.dataset.DataSetService.delete',
    )

    # act
    response = api_client.delete(f'/datasets/{dataset.id}')

    # assert
    assert response.status_code == 204
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        instance=dataset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    delete_mock.assert_called_once_with()
