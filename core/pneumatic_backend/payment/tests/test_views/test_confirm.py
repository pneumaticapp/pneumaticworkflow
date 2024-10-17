import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import TokenError
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.payment import messages
from pneumatic_backend.payment.stripe.tokens import ConfirmToken


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_confirm__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    token = ConfirmToken()
    token['user_id'] = user.id
    token['account_id'] = user.account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.API

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    confirm_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.confirm'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/confirm',
        data={
            'token': str(token),
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.API,
        is_superuser=False
    )
    confirm_mock.assert_called_once()


def test_confirm__subscription_data__ok(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    subscription_data = {
        'code': 'price code',
        'quantity': 2
    }
    token = ConfirmToken()
    token['user_id'] = user.id
    token['account_id'] = user.account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.API
    token['subscription'] = subscription_data

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    confirm_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.confirm'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/confirm',
        data={
            'token': str(token),
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        auth_type=AuthTokenType.API,
        is_superuser=False
    )
    confirm_mock.assert_called_once_with(
        subscription_data=subscription_data
    )


def test_confirm__skip_token__validation_error(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    confirm_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.confirm'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get('/payment/confirm')

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'token'
    service_init_mock.assert_not_called()
    confirm_mock.assert_not_called()


def test_confirm__invalid_token__validation_error(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    message = 'some message'
    get_token_mock = mocker.patch.object(
        ConfirmToken,
        attribute='__init__',
        side_effect=TokenError(message)
    )
    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    confirm_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.confirm'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=True
    )
    invalid_token = '!@#ASEwadd13'
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/confirm',
        data={
            'token': invalid_token,
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_BL_0001
    assert response.data['details']['reason'] == messages.MSG_BL_0001
    assert response.data['details']['name'] == 'token'
    get_token_mock.assert_called_once_with(invalid_token)
    service_init_mock.assert_not_called()
    confirm_mock.assert_not_called()


def test_confirm__disable_billing__permission_denied(
    mocker,
    api_client,
):
    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    token = ConfirmToken()
    token['user_id'] = user.id
    token['account_id'] = user.account.id
    token['is_superuser'] = False
    token['auth_type'] = AuthTokenType.API

    service_init_mock = mocker.patch.object(
        StripeService,
        attribute='__init__',
        return_value=None
    )
    confirm_mock = mocker.patch(
        'pneumatic_backend.payment.stripe.service.StripeService.confirm'
    )
    mocker.patch(
        'pneumatic_backend.payment.views.ProjectBillingPermission'
        '.has_permission',
        return_value=False
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/payment/confirm',
        data={
            'token': str(token),
        }
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    confirm_mock.assert_not_called()
    assert response.data['detail'] == messages.MSG_BL_0021
