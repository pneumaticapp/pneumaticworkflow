import pytest
from rest_framework.fields import Field

from src.ai.enums import AIVendor
from src.ai.exceptions import AIProviderException
from src.ai.services.provider import AIProviderService
from src.ai.tests.fixtures import create_test_provider
from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_by_vendor__all_fields__ok(api_client, mocker):

    """ Create provider by vendor """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers/by-vendor'
    data = {
        'api_key': 'sk-or-v1-example',
        'vendor': AIVendor.OPENROUTER,
    }
    provider = create_test_provider(account=account)
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_by_vendor_mock = mocker.patch(
        'src.ai.views.AIProviderService.create_by_vendor',
        return_value=provider,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['id'] == provider.id
    assert response.data['name'] == provider.name
    assert response.data['base_url'] == provider.base_url
    assert response.data['api_key_prefix'] == (
        provider.api_key_prefix
    )
    assert response.data['vendor'] == provider.vendor
    assert response.data['is_active'] is True
    assert response.data['usage'] == []
    assert 'api_key' not in response.data
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_by_vendor_mock.assert_called_once_with(
        api_key='sk-or-v1-example',
        vendor=AIVendor.OPENROUTER,
    )


def test_by_vendor__not_authenticated__unauthorized(
    api_client,
):

    """ Unauthenticated request """

    # arrange
    path = '/ai/providers/by-vendor'
    data = {
        'api_key': 'sk-or-v1-example',
        'vendor': AIVendor.OPENROUTER,
    }
    message = (
        'Authentication credentials were not provided.'
    )

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_by_vendor__not_admin__permission_denied(
    api_client,
):

    """ User is not admin and not account owner """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    path = '/ai/providers/by-vendor'
    data = {
        'api_key': 'sk-or-v1-example',
        'vendor': AIVendor.OPENROUTER,
    }
    message = (
        'You do not have permission to perform this action.'
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_by_vendor__missing_api_key__validation_error(
    api_client,
    mocker,
):

    """ Missing api_key field """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers/by-vendor'
    data = {
        'vendor': AIVendor.OPENROUTER,
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_by_vendor_mock = mocker.patch(
        'src.ai.views.AIProviderService.create_by_vendor',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(
        Field.default_error_messages['required'],
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'api_key'
    ai_provider_service_init_mock.assert_not_called()
    create_by_vendor_mock.assert_not_called()


def test_by_vendor__missing_vendor__validation_error(
    api_client,
    mocker,
):

    """ Missing vendor field """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers/by-vendor'
    data = {
        'api_key': 'sk-or-v1-example',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_by_vendor_mock = mocker.patch(
        'src.ai.views.AIProviderService.create_by_vendor',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(
        Field.default_error_messages['required'],
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'vendor'
    ai_provider_service_init_mock.assert_not_called()
    create_by_vendor_mock.assert_not_called()


def test_by_vendor__invalid_vendor__validation_error(
    api_client,
    mocker,
):

    """ Invalid vendor value """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers/by-vendor'
    invalid_vendor = 'invalid_vendor'
    data = {
        'api_key': 'sk-or-v1-example',
        'vendor': invalid_vendor,
    }
    message = (
        f'"{invalid_vendor}" is not a valid choice.'
    )
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_by_vendor_mock = mocker.patch(
        'src.ai.views.AIProviderService.create_by_vendor',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'vendor'
    ai_provider_service_init_mock.assert_not_called()
    create_by_vendor_mock.assert_not_called()


def test_by_vendor__service_exception__validation_error(
    api_client,
    mocker,
):

    """ Service raises AIProviderException """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers/by-vendor'
    data = {
        'api_key': 'sk-or-v1-example',
        'vendor': AIVendor.OPENROUTER,
    }
    error_message = 'AI service error'
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_by_vendor_mock = mocker.patch(
        'src.ai.views.AIProviderService.create_by_vendor',
        side_effect=AIProviderException(
            message=error_message,
        ),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_by_vendor_mock.assert_called_once_with(
        api_key='sk-or-v1-example',
        vendor=AIVendor.OPENROUTER,
    )
