import base64
import pytest

from src.authentication.services.auth0 import (
    Auth0Service,
)
from src.authentication.services.exceptions import (
    AuthException,
)
from src.processes.tests.fixtures import (
    create_test_owner,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_token__existent_user__authenticate(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    email = 'test@test.test'
    user = create_test_owner(email=email)
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    token = '!@#E213'
    domain = 'dev-123456.okta.com'
    state_uuid = 'YrtkHpALzeTDnliK'
    domain_encoded = base64.urlsafe_b64encode(
        domain.encode('utf-8'),
    ).decode('utf-8').rstrip('=')
    state = f"{state_uuid[:8]}{domain_encoded}"
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
        return_value=(user, token),
    )
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': state,
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        REMOTE_ADDR=user_ip,
    )

    # assert
    assert response.status_code == 200
    assert response.data['token'] == token
    auth0_service_init_mock.assert_called_once_with(domain=domain)
    authenticate_user_mock.assert_called_once_with(
        code=auth_response['code'],
        domain=domain,
        state=auth_response['state'],
        user_agent=user_agent,
        user_ip=user_ip,
    )


def test_token__disable_auth0_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
        'has_permission',
        return_value=False,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
    )
    user_agent = 'Some/Mozilla'
    user_ip = '128.18.0.99'
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': 'KvpfgTSUmwtOaPny',
    }

    # act
    response = api_client.get(
        '/auth/auth0/token',
        data=auth_response,
        HTTP_USER_AGENT=user_agent,
        REMOTE_ADDR=user_ip,
    )

    # assert
    assert response.status_code == 401
    auth0_service_init_mock.assert_not_called()
    authenticate_user_mock.assert_not_called()


def test_token__service_exception__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
    )
    message = 'Some error'
    authenticate_user_mock = mocker.patch(
        'src.authentication.services.auth0.'
        'Auth0Service.authenticate_user',
        side_effect=AuthException(message),
    )
    domain = 'dev-123456.okta.com'
    state_uuid = 'YrtkHpALzeTDnliK'
    domain_encoded = base64.urlsafe_b64encode(
        domain.encode('utf-8'),
    ).decode('utf-8').rstrip('=')
    state = f"{state_uuid[:8]}{domain_encoded}"
    auth_response = {
        'code': '0.Ab0Aa_jrV8Qkv...9UWtS972sufQ',
        'state': state,
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
    auth0_service_init_mock.assert_called_once_with(domain=domain)
    authenticate_user_mock.assert_called_once_with(
        code=auth_response['code'],
        state=auth_response['state'],
        domain=domain,
        user_agent=mocker.ANY,
        user_ip=mocker.ANY,
    )


def test_token__skip__code__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
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
    authenticate_user_mock.assert_not_called()


def test_token__code_blank__validation_error(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
        'has_permission',
        return_value=True,
    )
    auth0_service_init_mock = mocker.patch.object(
        Auth0Service,
        attribute='__init__',
        return_value=None,
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
    authenticate_user_mock.assert_not_called()


def test_auth_uri__ok(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
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
    auth0_service_init_mock.assert_called_once_with()
    auth0_get_auth_uri_mock.assert_called_once()


def test_auth_uri__disable_auth0_auth__permission_denied(
    mocker,
    api_client,
):
    # arrange
    mocker.patch(
        'src.authentication.views.auth0.SSOPermission.'
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
        'src.authentication.views.auth0.SSOPermission.'
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
