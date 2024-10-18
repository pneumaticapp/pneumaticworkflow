import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.payment import messages
from pneumatic_backend.payment.stripe.exceptions import (
    StripeServiceException,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_card_setup__payment_link__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    setup_link = 'checkout.stripe.com'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    card_setup_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_payment_method_checkout_link',
        return_value=setup_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/card-setup',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['setup_link'] == setup_link
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    card_setup_mock.assert_called_once_with(
        success_url=success_url,
        cancel_url=cancel_url
    )


def test_card_setup__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    card_setup_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_payment_method_checkout_link',
        side_effect=StripeServiceException(message)
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/card-setup',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
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
    card_setup_mock.assert_called_once_with(
        success_url=success_url,
        cancel_url=cancel_url
    )


def test_card_setup__success_url_is_skipped__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    cancel_url = 'http://localhost/cancel/'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    card_setup_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_payment_method_checkout_link'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/card-setup',
        data={
            'cancel_url': cancel_url,
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
    card_setup_mock.assert_not_called()


def test_card_setup__success_url_invalid__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    cancel_url = 'http://localhost/cancel/'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    card_setup_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_payment_method_checkout_link'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/card-setup',
        data={
            'cancel_url': cancel_url,
            'success_url': '/localhost/success'
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
    card_setup_mock.assert_not_called()


def test_card_setup__cancel_url_invalid__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/cancel/'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    card_setup_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_payment_method_checkout_link'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/card-setup',
        data={
            'cancel_url':  '/localhost/success',
            'success_url': success_url
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
    card_setup_mock.assert_not_called()


def test_card_setup__disable_billing__permission_denied(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    success_url = 'http://localhost/success/'
    cancel_url = 'http://localhost/cancel/'
    setup_link = 'checkout.stripe.com'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    card_setup_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_payment_method_checkout_link',
        return_value=setup_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/card-setup',
        data={
            'success_url': success_url,
            'cancel_url': cancel_url,
        }
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
    service_init_mock.assert_not_called()
    card_setup_mock.assert_not_called()
