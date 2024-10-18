import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.payment.services.account import (
    AccountSubscriptionService
)
from pneumatic_backend.payment.services.exceptions import (
    AccountServiceException
)
from pneumatic_backend.payment import messages
from pneumatic_backend.utils.validation import ErrorCode

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_downgrade_to_free__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    downgrade_to_free_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.downgrade_to_free',
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post('/payment/subscription/downgrade-to-free')

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        instance=user.account,
        user=user,
        is_superuser=False
    )
    downgrade_to_free_mock.assert_called_once()


def test_downgrade_to_free__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    downgrade_to_free_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.downgrade_to_free',
        side_effect=AccountServiceException(message)
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post('/payment/subscription/downgrade-to-free')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        instance=user.account,
        user=user,
        is_superuser=False
    )
    downgrade_to_free_mock.assert_called_once()


def test_downgrade_to_free__disable_billing__permission_denied(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        AccountSubscriptionService,
        attribute='__init__',
        return_value=None
    )
    downgrade_to_free_mock = mocker.patch(
        'pneumatic_backend.payment.services.account.'
        'AccountSubscriptionService.downgrade_to_free',
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post('/payment/subscription/downgrade-to-free')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
    service_init_mock.assert_not_called()
    downgrade_to_free_mock.assert_not_called()
