import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from pneumatic_backend.payment.enums import PriceStatus
from pneumatic_backend.payment.tests.fixtures import (
    create_test_recurring_price,
    create_test_invoice_price,
    create_test_product,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.exceptions import (
    StripeServiceException,
)
from pneumatic_backend.payment import messages
from pneumatic_backend.utils.validation import ErrorCode


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_purchase__payment_link__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    price = create_test_recurring_price()
    quantity = settings.PAYWALL_MIN_USERS
    payment_link = 'checkout.stripe.com'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase',
        return_value=payment_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
            'products': [
                {
                    'code': price.code,
                    'quantity': quantity
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['payment_link'] == payment_link
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        cancel_url=cancel_url,
        products=[
            {
                'code': price.code,
                'quantity': quantity
            }
        ]
    )


def test_purchase__off_session__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    price = create_test_recurring_price()
    quantity = user.account.max_users + 1

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.'
        'StripeService.create_purchase',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
            'products': [
                {
                    'code': price.code,
                    'quantity': quantity
                }
            ]
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        cancel_url=cancel_url,
        products=[
            {
                'code': price.code,
                'quantity': quantity
            }
        ]
    )


def test_purchase__archived_price__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    price = create_test_recurring_price(
        status=PriceStatus.ARCHIVED
    )
    quantity = settings.PAYWALL_MIN_USERS
    payment_link = 'checkout.stripe.com'

    mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase',
        return_value=payment_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
            'products': [
                {
                    'code': price.code,
                    'quantity': quantity
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['payment_link'] == payment_link


def test_purchase__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    price = create_test_recurring_price()
    quantity = settings.PAYWALL_MIN_USERS
    message = 'some error'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase',
        side_effect=StripeServiceException(message)
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
            'products': [
                {
                    'code': price.code,
                    'quantity': quantity
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    create_purchase_mock.assert_called_once_with(
        success_url=success_url,
        cancel_url=cancel_url,
        products=[
            {
                'code': price.code,
                'quantity': quantity
            }
        ]
    )


def test_purchase__empty_products__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'products': []
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0002
    assert response.data['details']['reason'] == messages.MSG_BL_0002
    assert response.data['details']['name'] == 'products'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__null_products__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'products': None
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'products'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__quantity_less_then_1__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'products': [
                {
                    'code': 'code',
                    'quantity': 0
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Ensure this value is greater than or equal to 1.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'quantity'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__success_url_is_skipped__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'products': [
                {
                    'code': 'code',
                    'quantity': 1
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'success_url'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__success_url_invalid__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': 'some str',
            'products': [
                {
                    'code': 'code',
                    'quantity': 1
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'success_url'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__cancel_url_invalid__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': 'http://localhost/success/',
            'cancel_url': '/localhost/',
            'products': [
                {
                    'code': 'code',
                    'quantity': 1
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'cancel_url'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__not_existent_product__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    price_code_1 = 'code_1'
    price_code_2 = 'code_2'
    price_code_3 = 'code_3'
    product = create_test_product(
        code='some code',
        stripe_id='product_123'
    )
    create_test_recurring_price(
        code=price_code_1,
        status=PriceStatus.INACTIVE,
        product=product,
    )
    create_test_invoice_price(
        code=price_code_3,
        status=PriceStatus.ACTIVE,
    )
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'products': [
                {
                    'code': price_code_2,
                    'quantity': 2
                },
                {
                    'code': price_code_3,
                    'quantity': 3
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_BL_0003(price_code_2)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'products'
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()


def test_purchase__not_existent_products__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    price_code_1 = 'code_1'
    price_code_2 = 'code_2'
    price_code_3 = 'code_3'
    product = create_test_product(
        code='some code',
        stripe_id='product_123'
    )
    create_test_recurring_price(
        code=price_code_1,
        status=PriceStatus.INACTIVE,
        product=product
    )
    create_test_invoice_price(
        code=price_code_3,
        status=PriceStatus.ACTIVE,
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'products': [
                {
                    'code': price_code_1,
                    'quantity': 1
                },
                {
                    'code': price_code_2,
                    'quantity': 2
                },
                {
                    'code': price_code_3,
                    'quantity': 3
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    error_codes = [price_code_1, price_code_2]
    reversed_error_codes = [price_code_2, price_code_1]
    message = messages.MSG_BL_0003(error_codes)
    message_reversed = messages.MSG_BL_0003(reversed_error_codes)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert (response.data['message'] == message) or (
        response.data['message'] == message_reversed
    )


def test_purchase__disable_billing__permission_denied(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    price = create_test_recurring_price()
    quantity = settings.PAYWALL_MIN_USERS
    payment_link = 'checkout.stripe.com'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    create_purchase_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.'
        'service.StripeService.create_purchase',
        return_value=payment_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/payment/purchase',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
            'products': [
                {
                    'code': price.code,
                    'quantity': quantity
                }
            ]
        }
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
    service_init_mock.assert_not_called()
    create_purchase_mock.assert_not_called()
