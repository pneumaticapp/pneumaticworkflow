import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.authentication.enums import AuthTokenType
from src.processes.services.exceptions import DataSetServiceException
from src.processes.services.templates.dataset import DataSetService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_dataset,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__unauthenticated__unauthorized(api_client):

    """Unauthenticated user — 401"""

    # arrange
    account = create_test_account()
    dataset = create_test_dataset(account=account)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 401


def test_partial_update__expired_subscription__permission_denied(api_client):

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
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_partial_update__billing_plan__permission_denied(api_client):

    """Billing plan restriction — 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_partial_update__users_overlimited__permission_denied(api_client):

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
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_partial_update__non_admin__permission_denied(api_client):

    """Non-admin/non-owner user — 403"""

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 403


def test_partial_update__not_found__not_found(api_client):

    """Non-existent dataset id — 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    non_existent_id = 999999

    # act
    response = api_client.patch(
        path=f'/datasets/{non_existent_id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 404


def test_partial_update__another_account__not_found(api_client):

    """Dataset belonging to another account — 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)

    another_account = create_test_account(name='Another Company')
    dataset = create_test_dataset(account=another_account)

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'Updated'},
    )

    # assert
    assert response.status_code == 404


def test_partial_update__name_too_long__validation_error(mocker, api_client):

    """`name` exceeds max length 200 — 400"""

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
    partial_update_mock = mocker.patch(
        'src.processes.services.templates'
        '.dataset.DataSetService.partial_update',
    )
    long_name = 'x' * 201

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': long_name},
    )

    # assert
    assert response.status_code == 400
    data_set_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()


def test_partial_update__item_value_too_long__validation_error(
    mocker,
    api_client,
):

    """`items[].value` exceeds max length 200 — 400"""

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
    partial_update_mock = mocker.patch(
        'src.processes.services.templates'
        '.dataset.DataSetService.partial_update',
    )
    data = {'items': [{'value': 'x' * 201}]}

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    data_set_service_init_mock.assert_not_called()
    partial_update_mock.assert_not_called()


def test_partial_update__minimal_data__ok(mocker, api_client):

    """Minimal valid request (one field) — 200"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account, name='Old Name')
    api_client.token_authenticate(user=user)
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.templates'
        '.dataset.DataSetService.partial_update',
        return_value=dataset,
    )

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data={'name': 'New Name'},
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == dataset.id
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        instance=dataset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        force_save=True,
        name='New Name',
    )


def test_partial_update__full_data__ok(mocker, api_client):

    """Full valid request (`name`, `description`, `items`) — 200"""

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
    partial_update_mock = mocker.patch(
        'src.processes.services.templates'
        '.dataset.DataSetService.partial_update',
        return_value=dataset,
    )
    items = [{'value': 'Updated item', 'order': 0}]
    data = {
        'name': 'Updated Name',
        'description': 'Updated description',
        'items': items,
    }

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == dataset.id
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        instance=dataset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        force_save=True,
        name='Updated Name',
        description='Updated description',
        items=items,
    )


def test_partial_update__service_exception__validation_error(
    mocker,
    api_client,
):

    """`DataSetServiceException` raised — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    dataset = create_test_dataset(account=account)
    api_client.token_authenticate(user=user)
    error_message = 'Dataset service error'
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.services.templates'
        '.dataset.DataSetService.partial_update',
        side_effect=DataSetServiceException(
            message=error_message,
        ),
    )
    data = {'name': 'Updated Name'}

    # act
    response = api_client.patch(
        path=f'/datasets/{dataset.id}',
        data=data,
    )

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
    partial_update_mock.assert_called_once_with(
        force_save=True,
        name='Updated Name',
    )
