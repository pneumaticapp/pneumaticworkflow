import socket

import pytest
from django.conf import settings
from rest_framework.fields import CharField, Field, URLField

from src.ai.exceptions import AIProviderException
from src.ai.messages import MSG_AI_0001, MSG_AI_0018
from src.ai.services.provider import AIProviderService
from src.ai.tests.fixtures import create_test_provider
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


def test_create__ok(api_client, mocker):

    """ Create provider """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'OpenRouter',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key': 'sk-or-v1-example',
    }
    provider = create_test_provider(account=account)
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
    assert 'api_key' not in response.data
    ai_provider_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_mock.assert_called_once_with(
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-example',
    )


def test_create__unauthenticated__unauthorized(api_client):

    """ Unauthenticated """

    # arrange
    path = '/ai/providers'
    data = {
        'name': 'OpenRouter',
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
        'name': 'OpenRouter',
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
        'name': 'OpenRouter',
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


def test_create__missing_name__validation_error(api_client, mocker):

    """ Missing name """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'base_url': 'https://openrouter.ai/api/v1',
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
    assert response.data['details']['name'] == 'name'
    ai_provider_service_init_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__missing_api_key__validation_error(api_client, mocker):

    """ Missing api_key """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'OpenRouter',
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
        'name': 'OpenRouter',
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
        'name': 'OpenRouter',
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


@pytest.mark.parametrize(
    'ip',
    (
        '127.0.0.1',
        '10.0.0.5',
        '172.18.0.7',
        '192.168.1.1',
        '169.254.169.254',
        '100.64.0.1',
        '0.0.0.0',
        '::1',
        'fe80::1%eth0',
        'fc00::1',
        '::ffff:127.0.0.1',
    ),
)
def test_create__base_url_not_public_ip__validation_error(
    ip,
    api_client,
    mocker,
    getaddrinfo_mock,
):

    """ base_url resolves to a non-public address """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'Internal',
        'base_url': 'http://internal.example.com:8888/dir?x=',
        'api_key': 'sk-or-v1-example',
    }
    family = socket.AF_INET6 if ':' in ip else socket.AF_INET
    getaddrinfo_mock.return_value = [
        (family, socket.SOCK_STREAM, 6, '', (ip, 0)),
    ]
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(path=path, data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(MSG_AI_0018)
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['name'] == 'base_url'
    getaddrinfo_mock.assert_called_once_with('internal.example.com', None)
    create_mock.assert_not_called()


def test_create__base_url_public_and_private_ip__validation_error(
    api_client,
    mocker,
    getaddrinfo_mock,
):

    """ base_url resolves to a public and a private address """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'Rebind',
        'base_url': 'https://rebind.example.com/v1',
        'api_key': 'sk-or-v1-example',
    }
    getaddrinfo_mock.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.5', 0)),
    ]
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(path=path, data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(MSG_AI_0018)
    assert response.data['details']['name'] == 'base_url'
    create_mock.assert_not_called()


def test_create__base_url_allowed_host__validation_error(
    api_client,
    mocker,
    getaddrinfo_mock,
):

    """ base_url points to one of the Pneumatic hosts """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    host = settings.ALLOWED_HOSTS[0]
    data = {
        'name': 'Pneumatic',
        'base_url': f'https://{host}/api',
        'api_key': 'sk-or-v1-example',
    }
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(path=path, data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(MSG_AI_0018)
    assert response.data['details']['name'] == 'base_url'
    getaddrinfo_mock.assert_not_called()
    create_mock.assert_not_called()


def test_create__base_url_not_resolved__validation_error(
    api_client,
    mocker,
    getaddrinfo_mock,
):

    """ base_url host is not resolved """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'Unknown',
        'base_url': 'https://no-such-host.invalid/v1',
        'api_key': 'sk-or-v1-example',
    }
    getaddrinfo_mock.side_effect = socket.gaierror(-2, 'Name not known')
    create_mock = mocker.patch(
        'src.ai.views.AIProviderService.create',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(path=path, data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == str(MSG_AI_0001)
    assert response.data['details']['name'] == 'base_url'
    create_mock.assert_not_called()


def test_create__base_url_too_long__validation_error(api_client, mocker):

    """ Base URL too long """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'OpenRouter',
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


def test_create__service_exception__validation_error(api_client, mocker):

    """ Service exception """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    path = '/ai/providers'
    data = {
        'name': 'OpenRouter',
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
        side_effect=AIProviderException(message=error_message),
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
        name='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-example',
    )
