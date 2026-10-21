import socket

import pytest
from rest_framework.fields import CharField, URLField

from src.ai.exceptions import AIProviderException
from src.ai.messages import MSG_AI_0018
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


def test_partial_update__minimal_data__ok(api_client, mocker):

    """ Minimal request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    updated_provider = AIProvider(
        account=account,
        name='Updated name',
        base_url='https://openrouter.ai/api/v1',
    )
    updated_provider.api_key = 'sk-or-v1-example'
    updated_provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated name',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
        return_value=updated_provider,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == updated_provider.id
    assert response.data['name'] == 'Updated name'
    assert 'api_key' not in response.data
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name='Updated name',
    )


def test_partial_update__full_data__ok(api_client, mocker):

    """ Full request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    updated_base_url = 'https://updated.example.com'
    updated_api_key = 'sk-or-v1-updated'
    updated_provider = AIProvider(
        account=account,
        name='OpenAI compatible',
        base_url=updated_base_url,
    )
    updated_provider.api_key = updated_api_key
    updated_provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'OpenAI compatible',
        'base_url': updated_base_url,
        'api_key': updated_api_key,
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
        return_value=updated_provider,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == updated_provider.id
    assert response.data['name'] == updated_provider.name
    assert response.data['base_url'] == updated_base_url
    assert 'api_key' not in response.data
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name='OpenAI compatible',
        base_url=updated_base_url,
        api_key=updated_api_key,
    )


def test_partial_update__unauthenticated__unauthorized(api_client):

    """ Unauthenticated """

    # arrange
    account = create_test_account()
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated',
    }
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_partial_update__guest__permission_denied(api_client):

    """ Guest user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
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
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated',
    }
    message = 'You do not have permission to perform this action.'
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.patch(
        path=path,
        data=data,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_partial_update__non_admin__permission_denied(api_client):

    """ Non-admin user """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated',
    }
    message = 'You do not have permission to perform this action.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message


def test_partial_update__not_found__not_found(api_client):

    """ Non-existent id """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    non_existent_id = 999999
    path = f'/ai/providers/{non_existent_id}'
    data = {
        'name': 'Updated',
    }
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_partial_update__another_account__not_found(api_client):

    """ Another account """

    # arrange
    account_1 = create_test_account()
    user = create_test_owner(account=account_1)
    account_2 = create_test_account(name='Another Company')
    provider = AIProvider(
        account=account_2,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated',
    }
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_partial_update__soft_deleted__not_found(api_client):

    """ Soft-deleted provider """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    provider.delete()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated',
    }
    message = 'Not found.'
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 404
    assert response.data['detail'] == message


def test_partial_update__empty_api_key__validation_error(api_client, mocker):

    """ Empty api_key """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'api_key': '',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
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
    partial_update_mock.assert_not_called()


def test_partial_update__invalid_base_url__validation_error(
    api_client,
    mocker,
):

    """ Invalid base_url """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'base_url': 'not-a-url',
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
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
    partial_update_mock.assert_not_called()


def test_partial_update__base_url_not_public_ip__validation_error(
    api_client,
    mocker,
    getaddrinfo_mock,
):

    """ base_url resolves to a non-public address """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'base_url': 'http://metadata.internal/latest',
    }
    getaddrinfo_mock.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('169.254.169.254', 0)),
    ]
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(path=path, data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(MSG_AI_0018)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'base_url'
    partial_update_mock.assert_not_called()


def test_partial_update__base_url_too_long__validation_error(
    api_client,
    mocker,
):

    """ Base URL too long """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'base_url': 'https://example.com/' + 'a' * 1024,
    }
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
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
    partial_update_mock.assert_not_called()


def test_partial_update__service_exception__validation_error(
    api_client,
    mocker,
):

    """ Service exception """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = AIProvider(
        account=account,
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
    )
    provider.api_key = 'sk-or-v1-example'
    provider.save()
    path = f'/ai/providers/{provider.id}'
    data = {
        'name': 'Updated name',
    }
    error_message = 'AI service error'
    ai_provider_service_init_mock = mocker.patch.object(
        AIProviderService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.ai.views.AIProviderService.partial_update',
        side_effect=AIProviderException(message=error_message),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        path=path,
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        instance=provider,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name='Updated name',
    )
