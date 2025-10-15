import pytest

from src.authentication.entities import UserData
from src.authentication.services.auth0 import (
    Auth0Service,
)
from src.authentication.services.exceptions import (
    AuthException,
)
from src.processes.tests.fixtures import create_test_account, create_test_user
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_token__existent_user__authenticate(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    email = 'test@test.test'
    user = create_test_user(email=email)
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
        return_value=(user, token),
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    update_auth0_contacts_mock = mocker.patch(
        'src.authentication.tasks.update_auth0_contacts.delay',
    )

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip,
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    authenticate_user_mock.assert_called_once_with(
        auth_response=auth_response,
        utm_source=None,
        utm_medium=None,
        utm_term=None,
        utm_content=None,
        gclid=None,
        utm_campaign=None,
    )
    update_auth0_contacts_mock.assert_called_once_with(user.id)


def test_token__disable_auth0_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=False,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    auth0_get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
    )
    save_tokens_for_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip,
    )

    # assert
    assert response.status_code == 401
    auth0_service_init_mock.assert_not_called()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()


def test_token__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some error'
    auth0_get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        side_effect=AuthException(message),
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
        side_effect=AuthException(message),
    )
    save_tokens_for_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_called_once()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_user_mock.assert_called_once()
    save_tokens_for_user_mock.assert_not_called()


def test_token__skip__code__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    auth0_get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
    )
    auth_response = {
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_not_called()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()


def test_token__code_blank__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    auth0_get_user_data_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_user_data',
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
    )
    auth_response = {
        'code': '',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_not_called()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()


def test_auth_uri__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    auth_uri = 'https://login.auth0.com/authorize'
    auth0_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_auth_uri',
        return_value=auth_uri,
    )

    # act
    response = api_client.get('/auth/auth0/auth-uri')

    # assert
    assert response.status_code == 200
    assert response.data['auth_uri'] == auth_uri
    auth0_service_init_mock.assert_called_once()
    auth0_get_auth_uri_mock.assert_called_once()


def test_auth_uri__disable_auth0_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=False,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    auth0_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_auth_uri',
    )

    # act
    response = api_client.get('/auth/auth0/auth-uri')

    # assert
    assert response.status_code == 401
    auth0_service_init_mock.assert_not_called()
    auth0_get_auth_uri_mock.assert_not_called()


def test_auth_uri__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some error'
    auth0_get_auth_uri_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.get_auth_uri',
        side_effect=AuthException(message),
    )

    # act
    response = api_client.get('/auth/auth0/auth-uri')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_called_once()
    auth0_get_auth_uri_mock.assert_called_once()


def test_token__join_existing_account__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    user = create_test_user(email='test@test.test')
    token = 'test_token'
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
        return_value=(user, token),
    )
    auth0_service_mock_instance = mocker.Mock()
    auth0_service_mock_instance.tokens = {
        'access_token': 'mock_access_token',
    }
    auth0_service_mock_instance.domain = 'mock-domain'
    auth0_service_mock_instance.client_id = 'mock-client-id'
    auth0_service_mock_instance.client_secret = 'mock-client-secret'
    auth0_service_mock_instance.redirect_uri = 'mock-redirect-uri'
    auth0_service_mock_instance.scope = 'mock-scope'
    mocker.patch(
        'src.authentication.views.auth0.Auth0Service',
        return_value=auth0_service_mock_instance,
    )
    email = 'test@test.test'
    user_data = UserData(
        email=email,
        first_name='Test',
        last_name='User',
        company_name='',
        photo=None,
        job_title='',
    )
    auth0_service_mock_instance.get_user_data = mocker.Mock(
        return_value=user_data,
    )
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value={'sub': 'test_user_id'},
    )
    organizations = [{'id': 'org_123', 'name': 'Test Org'}]
    auth0_service_mock_instance.get_user_organizations = mocker.Mock(
        return_value=organizations,
    )
    existing_account = create_test_account()
    existing_account.external_id = 'org_123'
    existing_account.save()
    auth0_service_mock_instance.authenticate_user = mocker.Mock(
        return_value=(user, token),
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    mocker.patch(
            'src.authentication.services.user_auth.'
            'AuthService.get_auth_token',
    )
    token = 'test_token'
    auth0_service_mock_instance.save_tokens_for_user = mocker.Mock()
    mocker.patch(
        'src.authentication.views.auth0.update_auth0_contacts.delay',
    )
    mocker.patch(
        'src.authentication.views.auth0.capture_sentry_message',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip,
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    auth0_service_mock_instance.authenticate_user.assert_called_once_with(
        auth_response={
            'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
            'state': 'KvpfgTSUmwtOaPny',
        },
        utm_source=None,
        utm_medium=None,
        utm_term=None,
        utm_content=None,
        gclid=None,
        utm_campaign=None,
    )


def test_token__create_new_account_with_external_id__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True,
    )
    user = create_test_user(email='test@test.test')
    token = 'test_token'
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
        return_value=(user, token),
    )
    auth0_service_mock_instance = mocker.Mock()
    auth0_service_mock_instance.tokens = {
        'access_token': 'mock_access_token',
    }
    auth0_service_mock_instance.domain = 'mock-domain'
    mocker.patch(
        'src.authentication.views.auth0.Auth0Service',
        return_value=auth0_service_mock_instance,
    )
    email = 'test@test.test'
    user_data = UserData(
        email=email,
        first_name='Test',
        last_name='User',
        company_name='',
        photo=None,
        job_title='',
    )
    auth0_service_mock_instance.get_user_data = mocker.Mock(
        return_value=user_data,
    )
    mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service._get_user_profile',
        return_value={'sub': 'test_user_id'},
    )
    organizations = [{'id': 'org_456', 'name': 'New Org'}]
    auth0_service_mock_instance.get_user_organizations = mocker.Mock(
        return_value=organizations,
    )
    auth0_service_mock_instance.authenticate_user = mocker.Mock(
        return_value=(user, token),
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    mocker.patch(
            'src.authentication.services.user_auth.'
            'AuthService.get_auth_token',
    )
    token = 'test_token'
    new_account = mocker.Mock()
    new_account.save = mocker.Mock()
    auth0_service_mock_instance.save_tokens_for_user = mocker.Mock()
    mocker.patch(
        'src.authentication.views.auth0.update_auth0_contacts.delay',
    )
    mocker.patch(
        'src.authentication.views.auth0.capture_sentry_message',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip,
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    auth0_service_mock_instance.authenticate_user.assert_called_once_with(
        auth_response={
            'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
            'state': 'KvpfgTSUmwtOaPny',
        },
        utm_source=None,
        utm_medium=None,
        utm_term=None,
        utm_content=None,
        gclid=None,
        utm_campaign=None,
    )
