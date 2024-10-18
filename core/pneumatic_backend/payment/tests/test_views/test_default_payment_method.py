import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.entities import CardDetails
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment import messages


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_default_payment_method__ok(
    api_client,
    mocker
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    last4 = '1234'
    brand = 'Maestro'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService'
        '.get_payment_method',
        return_value=CardDetails(last4=last4, brand=brand)
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/payment/default-payment-method')

    # assert
    assert response.status_code == 200
    assert response.data['last4'] == last4
    assert response.data['brand'] == brand
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    get_payment_method_mock.assert_called_once()


def test_default_payment_method__not_exist__not_found(
    api_client,
    mocker
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService'
        '.get_payment_method',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/payment/default-payment-method')

    # assert
    assert response.status_code == 404
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    get_payment_method_mock.assert_called_once()


def test_default_payment_method__disable_billing__permission_denied(
    api_client,
    mocker
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    last4 = '1234'
    brand = 'Maestro'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_payment_method_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService'
        '.get_payment_method',
        return_value=CardDetails(last4=last4, brand=brand)
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/payment/default-payment-method')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
    service_init_mock.assert_not_called()
    get_payment_method_mock.assert_not_called()
