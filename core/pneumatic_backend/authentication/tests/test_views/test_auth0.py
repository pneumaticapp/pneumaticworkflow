import pytest
from pneumatic_backend.authentication.services.exceptions import (
    AuthException
)
from pneumatic_backend.authentication.services.auth0 import (
    Auth0Service
)
from pneumatic_backend.authentication.entities import UserData
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_token__existent_user__authenticate(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user = create_test_user(email=email)
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
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
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    auth0_service_init_mock.assert_called_once()
    auth0_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_called_once_with(
        user=user,
        user_agent=user_agent,
        user_ip=user_ip,
    )
    save_tokens_for_user_mock.assert_called_once_with(user)


def test_token__disable_auth0_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=False
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data'
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token',
        return_value=token
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
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
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 401
    auth0_service_init_mock.assert_not_called()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()


def test_token__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    message = 'Some error'
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        side_effect=AuthException(message)
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'Auth0ViewSet.signup'
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_called_once()
    auth0_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()


def test_token__user_not_found__signup(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': True}
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token'
    )
    token = '!@#Eqa13d'
    user_mock = mocker.Mock(id='123')
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'Auth0ViewSet.signup',
        return_value=(user_mock, token)
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }
    utm_source = 'some_utm_source'
    utm_medium = 'some_utm_medium'
    utm_campaign = 'some_utm_campaign'
    utm_term = 'some_utm_term'
    utm_content = 'some_utm_content'
    gclid = 'some_gclid'

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data={
            **auth_response,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'utm_term': utm_term,
            'utm_content': utm_content,
            'gclid': gclid,
        },
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    auth0_service_init_mock.assert_called_once()
    auth0_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_not_called()
    signup_mock.assert_called_once_with(
        **user_data,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
        gclid=gclid,
    )
    save_tokens_for_user_mock.assert_called_once_with(user_mock)


def test_token__user_not_found_and_signup_disabled__authentication_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    settings_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.settings'
    )
    settings_mock.PROJECT_CONF = {'SIGNUP': False}
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    email = 'test@test.test'
    user_data = UserData(
        email=email,
        first_name='',
        last_name='',
        company_name='',
        photo=None,
        job_title=''
    )
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data',
        return_value=user_data
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token'
    )
    token = '!@#Eqa13d'
    user_mock = mocker.Mock(id='123')
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'Auth0ViewSet.signup',
        return_value=(user_mock, token)
    )
    save_tokens_for_user_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.save_tokens_for_user',
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data={**auth_response},
        HTTP_USER_AGENT=user_agent,
        HTTP_X_REAL_IP=user_ip
    )

    # assert
    assert response.status_code == 401
    auth0_service_init_mock.assert_called_once()
    auth0_get_user_data_mock.assert_called_once_with(
        auth_response=auth_response
    )
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()
    save_tokens_for_user_mock.assert_not_called()


def test_token__skip__code__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'Auth0ViewSet.signup'
    )
    auth_response = {
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_not_called()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_token__code_blank__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    auth0_get_user_data_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_user_data'
    )
    authenticate_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'AuthService.get_auth_token'
    )
    signup_mock = mocker.patch(
        'pneumatic_backend.authentication.views.auth0.'
        'Auth0ViewSet.signup'
    )
    auth_response = {
        'code': '',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_not_called()
    auth0_get_user_data_mock.assert_not_called()
    authenticate_mock.assert_not_called()
    signup_mock.assert_not_called()


def test_auth_uri__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    auth_uri = 'https://login.auth0.com/authorize'
    auth0_get_auth_uri_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_auth_uri',
        return_value=auth_uri
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
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=False
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    auth0_get_auth_uri_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_auth_uri'
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
        'pneumatic_backend.authentication.views.auth0.Auth0Permission.'
        'has_permission',
        return_value=True
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None
    )
    message = 'Some error'
    auth0_get_auth_uri_mock = mocker.patch(
        'pneumatic_backend.authentication.services.auth0.'
        'Auth0Service.get_auth_uri',
        side_effect=AuthException(message)
    )

    # act
    response = api_client.get('/auth/auth0/auth-uri')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    auth0_service_init_mock.assert_called_once()
    auth0_get_auth_uri_mock.assert_called_once()
