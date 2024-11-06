import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment import messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.payment.stripe.exceptions import (
    StripeServiceException,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_get_customer_portal_link__ok(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    cancel_url = 'http://localhost/cancel/'
    customer_portal_link = 'checkout.stripe.com/portal?token=123wsd'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link',
        return_value=customer_portal_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/customer-portal',
        data={
            'cancel_url': cancel_url,
        }
    )

    # assert
    assert response.status_code == 200
    assert response.data['link'] == customer_portal_link
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False
    )
    get_customer_portal_link_mock.assert_called_once_with(
        cancel_url=cancel_url
    )


def test_get_customer_portal_link__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    cancel_url = 'http://localhost/cancel/'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    message = 'some message'
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link',
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
        '/payment/customer-portal',
        data={
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
    get_customer_portal_link_mock.assert_called_once_with(
        cancel_url=cancel_url
    )


def test_get_customer_portal_link__invalid_cancel_url__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    cancel_url = '/localhost/cancel/'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/customer-portal',
        data={
            'cancel_url': cancel_url
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
    get_customer_portal_link_mock.assert_not_called()


def test_get_customer_portal_link__skip_cancel_url__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user(is_account_owner=True)

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/customer-portal'
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'cancel_url'
    service_init_mock.assert_not_called()
    get_customer_portal_link_mock.assert_not_called()


def test_get_customer_portal_link__cancel_url_is_null__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user(is_account_owner=True)
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/customer-portal?cancel_url=null'
    )

    # assert
    assert response.status_code == 400
    message = 'Enter a valid URL.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'cancel_url'
    service_init_mock.assert_not_called()
    get_customer_portal_link_mock.assert_not_called()


def test_get_customer_portal_link__not_account_owner__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account_owner = create_test_user(is_account_owner=True)
    user = create_test_user(
        is_account_owner=False,
        account=account_owner.account,
        email='admin@test.test'
    )
    cancel_url = 'http://localhost/cancel/'
    customer_portal_link = 'checkout.stripe.com/portal?token=123wsd'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link',
        return_value=customer_portal_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/customer-portal',
        data={
            'cancel_url': cancel_url,
        }
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    get_customer_portal_link_mock.assert_not_called()


def test__disable_billing__permission_denied(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user(is_account_owner=True)
    cancel_url = 'http://localhost/cancel/'
    customer_portal_link = 'checkout.stripe.com/portal?token=123wsd'

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    get_customer_portal_link_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.'
        'get_customer_portal_link',
        return_value=customer_portal_link
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/customer-portal',
        data={
            'cancel_url': cancel_url,
        }
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_BL_0021
    service_init_mock.assert_not_called()
    get_customer_portal_link_mock.assert_not_called()
