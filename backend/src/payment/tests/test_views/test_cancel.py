import pytest
from django.contrib.auth import get_user_model
from src.processes.tests.fixtures import (
    create_test_user,
)
from src.authentication.enums import AuthTokenType
from src.payment.stripe.service import StripeService
from src.payment.stripe.exceptions import (
    StripeServiceException,
)
from src.payment import messages
from src.utils.validation import ErrorCode

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_cancel_subscription__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True,
    )
    cancel_subscription_mock = mocker.patch(
        'src.payment.stripe.'
        'service.StripeService.cancel_subscription',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/payment/subscription/cancel')

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    cancel_subscription_mock.assert_called_once()


def test_cancel_service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    message = 'some message'
    mocker.patch(
        'src.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True,
    )
    cancel_subscription_mock = mocker.patch(
        'src.payment.stripe.'
        'service.StripeService.cancel_subscription',
        side_effect=StripeServiceException(message),
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/payment/subscription/cancel')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    cancel_subscription_mock.assert_called_once()


def test_cancel_subscription__disable_billing__permission_denied(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    mocker.patch(
        'src.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False,
    )
    cancel_subscription_mock = mocker.patch(
        'src.payment.stripe.'
        'service.StripeService.cancel_subscription',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post('/payment/subscription/cancel')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
    service_init_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()
