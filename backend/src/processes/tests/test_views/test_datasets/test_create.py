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


def test_create__unauthenticated__unauthorized(api_client):

    """Unauthenticated user — 401"""

    # arrange
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 401


def test_create__expired_subscription__permission_denied(api_client):

    """Expired subscription — 403"""

    # arrange

    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_create__billing_plan__permission_denied(api_client):

    """Billing plan restriction — 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_create__users_overlimited__permission_denied(api_client):

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
    api_client.token_authenticate(user=user)
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_create__non_admin__permission_denied(api_client):

    """Non-admin/non-owner user — 403"""

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user=user)
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 403


def test_create__missing_name__validation_error(mocker, api_client):

    """Missing required field `name` — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.dataset.DataSetService.create',
    )

    # act
    response = api_client.post(
        path='/datasets',
        data={},
    )

    # assert
    assert response.status_code == 400
    data_set_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__name_too_long__validation_error(mocker, api_client):

    """`name` exceeds max length 200 — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.dataset.DataSetService.create',
    )
    long_name = 'x' * 201

    # act
    response = api_client.post(
        path='/datasets',
        data={'name': long_name},
    )

    # assert
    assert response.status_code == 400
    data_set_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__item_value_too_long__validation_error(mocker, api_client):

    """`items[].value` exceeds max length 200 — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.dataset.DataSetService.create',
    )
    data = {
        'name': 'Dataset',
        'items': [{'value': 'x' * 201}],
    }

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 400
    data_set_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__minimal_data__ok(mocker, api_client):

    """Minimal valid request (only `name`) — 201"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    dataset = create_test_dataset(
        account=account,
        name='New Dataset',
        items_count=0,
    )
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.dataset.DataSetService.create',
        return_value=dataset,
    )
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['id'] == dataset.id
    assert response.data['name'] == dataset.name
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='New Dataset',
        description='',
        items=[],
    )


def test_create__full_data__ok(mocker, api_client):

    """Full valid request (`name`, `description`, `items`) — 201"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    dataset = create_test_dataset(
        account=account,
        name='Full Dataset',
        description='A description',
        items_count=1,
    )
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.dataset.DataSetService.create',
        return_value=dataset,
    )
    items = [{'value': 'Item 1', 'order': 1}]
    data = {
        'name': 'Full Dataset',
        'description': 'A description',
        'items': items,
    }

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['id'] == dataset.id
    assert response.data['name'] == dataset.name
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='Full Dataset',
        description='A description',
        items=items,
    )


def test_create__service_exception__validation_error(mocker, api_client):

    """`DataSetServiceException` raised — 400"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    error_message = 'Dataset service error'
    data_set_service_init_mock = mocker.patch.object(
        DataSetService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.processes.services.templates.dataset.DataSetService.create',
        side_effect=DataSetServiceException(message=error_message),
    )
    data = {'name': 'New Dataset'}

    # act
    response = api_client.post(
        path='/datasets',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    data_set_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='New Dataset',
        description='',
        items=[],
    )
