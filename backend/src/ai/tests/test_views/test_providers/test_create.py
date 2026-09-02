import pytest
from rest_framework.fields import BooleanField, CharField, Field, URLField

from src.ai.exceptions import AIServiceException
from src.ai.models import AIProvider
from src.ai.services.provider import AIProviderService
from src.authentication.enums import AuthTokenType
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_create__minimal_data__ok(api_client, mocker):

    """ Minimal request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    }
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=True,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
    assert response.data['is_active'] is True
    assert 'api_key' not in response.data
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-example',
        is_active=True,
    )


def test_create__full_data__ok(api_client, mocker):

    """ Full request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
        'is_active': False,
    }
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        is_active=False,
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
    assert set(response.data.keys()) == {
        'id',
        'name',
        'base_url',
        'api_key_prefix',
        'vendor',
        'is_active',
        'usage',
    }
    assert response.data['id'] == provider.id
    assert response.data['name'] == provider.name
    assert response.data['base_url'] == provider.base_url
    assert response.data['is_active'] is False
    assert 'api_key' not in response.data
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-example',
        is_active=False,
    )


def test_create__unauthenticated__unauthorized(api_client):

    """ Unauthenticated """

    # arrange
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    }
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_create__guest__permission_denied(api_client):

    """ Guest user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    }
    message = 'You do not have permission to perform this action.'
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.post(
        path=path,
        data=data,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_create__non_admin__permission_denied(api_client):

    """ Non-admin user """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    }
    message = 'You do not have permission to perform this action.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_create__missing_base_url__validation_error(api_client, mocker):

    """ Missing base_url """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'OpenRouter',
        'api_key': 'sk-or-v1-example',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
    assert response.data['details']['name'] == 'base_url'
    ai_provider_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__missing_api_key__validation_error(api_client, mocker):

    """ Missing api_key """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
    create_mock.assert_not_called()


def test_create__empty_api_key__validation_error(api_client, mocker):

    """ Empty api_key """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': '',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
        CharField.default_error_messages['blank'],
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'api_key'
    ai_provider_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__invalid_base_url__validation_error(api_client, mocker):

    """ Invalid base_url """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'not-a-url',
        'api_key': 'sk-or-v1-example',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
        URLField.default_error_messages['invalid'],
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'base_url'
    ai_provider_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__base_url_too_long__validation_error(api_client, mocker):

    """ Base URL too long """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://example.com/' + 'a' * 1024,
        'api_key': 'sk-or-v1-example',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
        CharField.default_error_messages['max_length'],
    ).format(max_length=1024)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'base_url'
    ai_provider_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__invalid_is_active__validation_error(api_client, mocker):

    """ Invalid is_active """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
        'is_active': 'not-a-boolean',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
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
        BooleanField.default_error_messages['invalid'],
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'is_active'
    ai_provider_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__service_exception__validation_error(api_client, mocker):

    """ Service exception """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    }
    error_message = 'AI service error'
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
        side_effect=AIServiceException(message=error_message),
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
    create_mock.assert_called_once_with(
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-example',
        is_active=True,
    )
