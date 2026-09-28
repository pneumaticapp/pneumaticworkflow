import pytest

from src.authentication.enums import AuthTokenType
from src.payment import messages
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_cancel__owner__audit_subscription_cancelled(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
    )
    subscription_cancelled_mock = mocker.patch(
        'src.payment.views.AuditEventService.subscription_cancelled',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 204
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    cancel_subscription_mock.assert_called_once_with()
    subscription_cancelled_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
    )


def test_cancel__admin__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    admin = create_test_admin()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
    )
    subscription_cancelled_mock = mocker.patch(
        'src.payment.views.AuditEventService.subscription_cancelled',
    )
    api_client.token_authenticate(user=admin)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 403
    stripe_service_init_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()
    subscription_cancelled_mock.assert_not_called()


def test_cancel__service_exception__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
        side_effect=StripeServiceException(message=messages.MSG_BL_0005),
    )
    subscription_cancelled_mock = mocker.patch(
        'src.payment.views.AuditEventService.subscription_cancelled',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0005
    assert response.data['details'] == {}
    stripe_service_init_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    cancel_subscription_mock.assert_called_once_with()
    subscription_cancelled_mock.assert_not_called()


def test_cancel__billing_sync_off__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(billing_sync=False)
    owner = create_test_owner(account=account)
    stripe_service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None,
    )
    cancel_subscription_mock = mocker.patch.object(
        StripeService,
        attribute='cancel_subscription',
    )
    subscription_cancelled_mock = mocker.patch(
        'src.payment.views.AuditEventService.subscription_cancelled',
    )
    api_client.token_authenticate(user=owner)

    # act
    response = api_client.post(path='/payment/subscription/cancel')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0018
    assert response.data['details'] == {}
    stripe_service_init_mock.assert_not_called()
    cancel_subscription_mock.assert_not_called()
    subscription_cancelled_mock.assert_not_called()
