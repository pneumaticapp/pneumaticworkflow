import pytest
from django.contrib.auth import get_user_model

from src.authentication.enums import AuthTokenType
from src.payment.stripe.entities import CardDetails
from src.payment.stripe.service import StripeService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_default_payment_method__ok(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    last4 = '1234'
    brand = 'Maestro'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    get_payment_method_mock = mocker.patch(
        'src.payment.stripe.service.StripeService'
        '.get_payment_method',
        return_value=CardDetails(last4=last4, brand=brand),
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
        is_superuser=False,
    )
    get_payment_method_mock.assert_called_once()


def test_default_payment_method__not_exist__not_found(
    api_client,
    mocker,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    get_payment_method_mock = mocker.patch(
        'src.payment.stripe.service.StripeService'
        '.get_payment_method',
        return_value=None,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/payment/default-payment-method')

    # assert
    assert response.status_code == 404
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    get_payment_method_mock.assert_called_once()
